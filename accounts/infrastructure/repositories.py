from datetime import datetime, timedelta
from typing import List

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from accounts.application.ports.out_ports import (
    LoadAccountPort,
    UpdateAccountStatePort,
    AccountLockPort,
    LoadTransactionHistoryPort,
    SaveTransactionPort,
    LoadAccountLimitsPort,
    UpdateAccountLimitsPort,
    SaveAccountStatementPort,
    LoadAccountStatementsPort
)
from accounts.domain.models import (
    Account, AccountId, Activity, ActivityWindow,
    Transaction, TransactionHistory, AccountLimits,
    DailyLimit, AccountStatement, StatementPeriod
)
from accounts.domain.value_objects import Money
from .models import (
    AccountModel, ActivityModel, TransactionModel,
    DailyLimitModel, AccountStatementModel
)


class DjangoAccountRepository(
    LoadAccountPort,
    UpdateAccountStatePort,
    LoadTransactionHistoryPort,
    SaveTransactionPort,
    LoadAccountLimitsPort,
    UpdateAccountLimitsPort,
    SaveAccountStatementPort,
    LoadAccountStatementsPort
):
    def load_account(self, account_id: AccountId, baseline_date: datetime) -> Account:
        try:
            account = AccountModel.objects.get(id=account_id.value)
        except AccountModel.DoesNotExist:
            raise ValueError(f"アカウントが見つかりません: {account_id.value}")

        activities = ActivityModel.objects.filter(
            owner_account_id=account_id.value,
            timestamp__gte=baseline_date
        )

        # baseline_date以前の残高を計算
        withdrawal_balance = ActivityModel.objects.filter(
            source_account_id=account_id.value,
            timestamp__lt=baseline_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        deposit_balance = ActivityModel.objects.filter(
            target_account_id=account_id.value,
            timestamp__lt=baseline_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        baseline_balance = Money(deposit_balance - withdrawal_balance)
        
        return Account.with_id(
            account_id=account_id,
            baseline_balance=baseline_balance,
            activity_window=self._map_to_activity_window(activities)
        )

    def update_activities(self, account: Account) -> None:
        with transaction.atomic():
            for activity in account.activity_window.activities:
                if activity.id is None:  # 新規アクティビティのみ保存
                    ActivityModel.objects.create(
                        owner_account_id=activity.owner_account_id.value,
                        source_account_id=activity.source_account_id.value,
                        target_account_id=activity.target_account_id.value,
                        timestamp=activity.timestamp,
                        amount=activity.money.amount
                    )

    def load_transaction_history(self, account_id: AccountId) -> TransactionHistory:
        transactions = TransactionModel.objects.filter(
            source_account_id=account_id.value
        ) | TransactionModel.objects.filter(
            target_account_id=account_id.value
        )
        
        return TransactionHistory(
            transactions=[
                Transaction(
                    id=None,
                    source_account_id=AccountId(tx.source_account_id),
                    target_account_id=AccountId(tx.target_account_id),
                    money=Money(tx.amount),
                    timestamp=tx.timestamp,
                    status=tx.status
                )
                for tx in transactions
            ],
            account_id=account_id
        )

    def save_transaction(self, transaction: Transaction) -> None:
        TransactionModel.objects.create(
            source_account_id=transaction.source_account_id.value,
            target_account_id=transaction.target_account_id.value,
            amount=transaction.money.amount,
            timestamp=transaction.timestamp,
            status=transaction.status
        )

    def load_account_limits(self, account_id: AccountId) -> AccountLimits:
        try:
            account = AccountModel.objects.get(id=account_id.value)
            daily_limit = account.daily_limit
            return AccountLimits(
                account_id=account_id,
                daily_limit=DailyLimit(
                    amount=Money(daily_limit.amount),
                    used_amount=Money(daily_limit.used_amount),
                    reset_time=daily_limit.reset_time
                ),
                minimum_balance=Money(account.minimum_balance),
                maximum_balance=Money(account.maximum_balance)
            )
        except (AccountModel.DoesNotExist, DailyLimitModel.DoesNotExist):
            # デフォルト値を返す
            return AccountLimits(
                account_id=account_id,
                daily_limit=DailyLimit(
                    amount=Money(1_000_000),
                    used_amount=Money(0),
                    reset_time=timezone.now() + timedelta(days=1)
                ),
                minimum_balance=Money(0),
                maximum_balance=Money(1_000_000_000)
            )

    def update_account_limits(self, account_limits: AccountLimits) -> None:
        with transaction.atomic():
            account = AccountModel.objects.get(id=account_limits.account_id.value)
            account.minimum_balance = account_limits.minimum_balance.amount
            account.maximum_balance = account_limits.maximum_balance.amount
            account.save()

            DailyLimitModel.objects.update_or_create(
                account=account,
                defaults={
                    'amount': account_limits.daily_limit.amount.amount,
                    'used_amount': account_limits.daily_limit.used_amount.amount,
                    'reset_time': account_limits.daily_limit.reset_time
                }
            )

    def save_account_statement(self, statement: AccountStatement) -> None:
        AccountStatementModel.objects.create(
            account_id=statement.account_id.value,
            start_date=statement.period.start_date,
            end_date=statement.period.end_date,
            opening_balance=statement.opening_balance.amount,
            closing_balance=statement.closing_balance.amount
        )

    def load_account_statements(
        self,
        account_id: AccountId,
        period: StatementPeriod
    ) -> List[AccountStatement]:
        statements = AccountStatementModel.objects.filter(
            account_id=account_id.value,
            start_date__gte=period.start_date,
            end_date__lte=period.end_date
        )
        
        return [
            AccountStatement(
                account_id=account_id,
                period=StatementPeriod(
                    start_date=stmt.start_date,
                    end_date=stmt.end_date
                ),
                transactions=self.load_transaction_history(
                    account_id
                ).get_transactions_in_period(
                    stmt.start_date,
                    stmt.end_date
                ),
                opening_balance=Money(stmt.opening_balance),
                closing_balance=Money(stmt.closing_balance)
            )
            for stmt in statements
        ]

    def _map_to_activity_window(self, activities: List[ActivityModel]) -> ActivityWindow:
        return ActivityWindow([
            Activity(
                id=None,  # IDは不要
                owner_account_id=AccountId(activity.owner_account_id),
                source_account_id=AccountId(activity.source_account_id),
                target_account_id=AccountId(activity.target_account_id),
                timestamp=activity.timestamp,
                money=Money(activity.amount)
            )
            for activity in activities
        ])


class NoOpAccountLock(AccountLockPort):
    """
    アカウントのロック機能の簡易実装
    実運用では、より堅牢なロック機構を実装する必要があります
    """
    def lock_account(self, account_id: AccountId) -> None:
        pass

    def release_account(self, account_id: AccountId) -> None:
        pass 