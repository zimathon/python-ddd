from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from .value_objects import Money


@dataclass
class AccountId:
    """口座IDを表す値オブジェクト"""
    value: int


@dataclass
class ActivityId:
    """取引活動IDを表す値オブジェクト"""
    value: int


@dataclass
class TransactionId:
    """取引IDを表す値オブジェクト"""
    value: int


@dataclass
class Activity:
    """取引活動を表すエンティティ"""
    id: Optional[ActivityId]
    owner_account_id: AccountId
    source_account_id: AccountId
    target_account_id: AccountId
    timestamp: datetime
    money: Money

    @classmethod
    def new_activity(
        cls,
        owner_account_id: AccountId,
        source_account_id: AccountId,
        target_account_id: AccountId,
        money: Money
    ) -> 'Activity':
        return cls(
            id=None,
            owner_account_id=owner_account_id,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            timestamp=datetime.now(),
            money=money
        )


@dataclass
class ActivityWindow:
    """取引活動の期間を管理するエンティティ"""
    activities: List[Activity]

    def get_start_timestamp(self) -> datetime:
        return min(activity.timestamp for activity in self.activities)

    def get_end_timestamp(self) -> datetime:
        return max(activity.timestamp for activity in self.activities)

    def calculate_balance(self, account_id: AccountId) -> Money:
        deposit_balance = sum(
            activity.money.amount
            for activity in self.activities
            if activity.target_account_id.value == account_id.value
        )
        withdrawal_balance = sum(
            activity.money.amount
            for activity in self.activities
            if activity.source_account_id.value == account_id.value
        )
        return Money(deposit_balance - withdrawal_balance)

    def add_activity(self, activity: Activity) -> None:
        self.activities.append(activity)


@dataclass
class Account:
    """口座を表すエンティティ"""
    id: Optional[AccountId]
    baseline_balance: Money
    activity_window: ActivityWindow

    @classmethod
    def without_id(
        cls,
        baseline_balance: Money,
        activity_window: ActivityWindow
    ) -> 'Account':
        return cls(
            id=None,
            baseline_balance=baseline_balance,
            activity_window=activity_window
        )

    @classmethod
    def with_id(
        cls,
        account_id: AccountId,
        baseline_balance: Money,
        activity_window: ActivityWindow
    ) -> 'Account':
        return cls(
            id=account_id,
            baseline_balance=baseline_balance,
            activity_window=activity_window
        )

    def calculate_balance(self) -> Money:
        return Money.add(
            self.baseline_balance,
            self.activity_window.calculate_balance(self.id)
        )

    def withdraw(self, money: Money, target_account_id: AccountId) -> bool:
        if not self._may_withdraw(money):
            return False

        withdrawal = Activity.new_activity(
            owner_account_id=self.id,
            source_account_id=self.id,
            target_account_id=target_account_id,
            money=money
        )
        self.activity_window.add_activity(withdrawal)
        return True

    def deposit(self, money: Money, source_account_id: AccountId) -> bool:
        deposit = Activity.new_activity(
            owner_account_id=self.id,
            source_account_id=source_account_id,
            target_account_id=self.id,
            money=money
        )
        self.activity_window.add_activity(deposit)
        return True

    def _may_withdraw(self, money: Money) -> bool:
        return Money.add(
            self.calculate_balance(),
            money.negate()
        ).is_positive_or_zero()


@dataclass
class Transaction:
    """取引を表すエンティティ"""
    id: Optional[TransactionId]
    source_account_id: AccountId
    target_account_id: AccountId
    money: Money
    timestamp: datetime
    status: 'TransactionStatus'

    @classmethod
    def new_transaction(
        cls,
        source_account_id: AccountId,
        target_account_id: AccountId,
        money: Money
    ) -> 'Transaction':
        return cls(
            id=None,
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            money=money,
            timestamp=datetime.now(),
            status=TransactionStatus.PENDING
        )


@dataclass
class TransactionStatus:
    """取引状態を表す値オブジェクト"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class TransactionHistory:
    """取引履歴を表すエンティティ"""
    transactions: List[Transaction]
    account_id: AccountId

    def get_transactions_in_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Transaction]:
        return [
            tx for tx in self.transactions
            if start_date <= tx.timestamp <= end_date
        ]

    def get_total_sent(self) -> Money:
        sent_amount = sum(
            tx.money.amount
            for tx in self.transactions
            if tx.source_account_id == self.account_id
            and tx.status == TransactionStatus.COMPLETED
        )
        return Money(sent_amount)

    def get_total_received(self) -> Money:
        received_amount = sum(
            tx.money.amount
            for tx in self.transactions
            if tx.target_account_id == self.account_id
            and tx.status == TransactionStatus.COMPLETED
        )
        return Money(received_amount)

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)


@dataclass
class TransactionSummary:
    """取引サマリーを表す値オブジェクト"""
    total_sent: Money
    total_received: Money
    net_balance: Money
    transaction_count: int

    @classmethod
    def from_history(cls, history: TransactionHistory) -> 'TransactionSummary':
        total_sent = history.get_total_sent()
        total_received = history.get_total_received()
        return cls(
            total_sent=total_sent,
            total_received=total_received,
            net_balance=Money.subtract(total_received, total_sent),
            transaction_count=len(history.transactions)
        )


@dataclass
class StatementPeriod:
    """明細期間を表す値オブジェクト"""
    start_date: datetime
    end_date: datetime

    def contains(self, date: datetime) -> bool:
        return self.start_date <= date <= self.end_date


@dataclass
class AccountStatement:
    """取引明細を表すエンティティ"""
    account_id: AccountId
    period: StatementPeriod
    transactions: List[Transaction]
    opening_balance: Money
    closing_balance: Money

    @classmethod
    def create_for_account(
        cls,
        account_id: AccountId,
        period: StatementPeriod,
        transaction_history: TransactionHistory,
        opening_balance: Money
    ) -> 'AccountStatement':
        transactions = transaction_history.get_transactions_in_period(
            period.start_date,
            period.end_date
        )
        
        # 期間内の取引から残高を計算
        balance_change = sum(
            tx.money.amount
            for tx in transactions
            if tx.status == TransactionStatus.COMPLETED
            and (
                (tx.target_account_id == account_id) or
                (-tx.money.amount if tx.source_account_id == account_id else 0)
            )
        )
        
        closing_balance = Money.add(
            opening_balance,
            Money(balance_change)
        )

        return cls(
            account_id=account_id,
            period=period,
            transactions=transactions,
            opening_balance=opening_balance,
            closing_balance=closing_balance
        )


@dataclass
class DailyLimit:
    """1日あたりの取引制限を表す値オブジェクト"""
    amount: Money
    used_amount: Money
    reset_time: datetime

    def can_withdraw(self, amount: Money) -> bool:
        return Money.add(self.used_amount, amount).amount <= self.amount.amount

    def add_withdrawal(self, amount: Money) -> None:
        self.used_amount = Money.add(self.used_amount, amount)


@dataclass
class AccountLimits:
    """口座の取引制限を表すエンティティ"""
    account_id: AccountId
    daily_limit: DailyLimit
    minimum_balance: Money
    maximum_balance: Money

    def can_withdraw(self, current_balance: Money, amount: Money) -> bool:
        after_withdrawal = Money.subtract(current_balance, amount)
        return (
            after_withdrawal.amount >= self.minimum_balance.amount and
            self.daily_limit.can_withdraw(amount)
        )

    def can_deposit(self, current_balance: Money, amount: Money) -> bool:
        after_deposit = Money.add(current_balance, amount)
        return after_deposit.amount <= self.maximum_balance.amount

    def record_withdrawal(self, amount: Money) -> None:
        self.daily_limit.add_withdrawal(amount) 