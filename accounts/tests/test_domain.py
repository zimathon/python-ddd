from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase

from accounts.domain.models import (
    Account, AccountId, Activity, ActivityWindow,
    Transaction, TransactionHistory, AccountLimits,
    DailyLimit, StatementPeriod, AccountStatement
)
from accounts.domain.value_objects import Money


class MoneyTest(TestCase):
    def test_add_money(self):
        """Money加算のテスト"""
        money1 = Money(Decimal('100'))
        money2 = Money(Decimal('200'))
        result = Money.add(money1, money2)
        self.assertEqual(result.amount, Decimal('300'))

    def test_subtract_money(self):
        """Money減算のテスト"""
        money1 = Money(Decimal('200'))
        money2 = Money(Decimal('100'))
        result = Money.subtract(money1, money2)
        self.assertEqual(result.amount, Decimal('100'))

    def test_negate_money(self):
        """Money否定のテスト"""
        money = Money(Decimal('100'))
        result = money.negate()
        self.assertEqual(result.amount, Decimal('-100'))


class AccountTest(TestCase):
    def setUp(self):
        self.account_id = AccountId(1)
        self.activity_window = ActivityWindow([])
        self.account = Account.with_id(
            account_id=self.account_id,
            baseline_balance=Money(Decimal('1000')),
            activity_window=self.activity_window
        )

    def test_calculate_balance(self):
        """残高計算のテスト"""
        self.assertEqual(
            self.account.calculate_balance().amount,
            Decimal('1000')
        )

    def test_withdraw_success(self):
        """出金成功のテスト"""
        result = self.account.withdraw(
            Money(Decimal('500')),
            AccountId(2)
        )
        self.assertTrue(result)
        self.assertEqual(
            self.account.calculate_balance().amount,
            Decimal('500')
        )

    def test_withdraw_failure(self):
        """出金失敗のテスト（残高不足）"""
        result = self.account.withdraw(
            Money(Decimal('2000')),
            AccountId(2)
        )
        self.assertFalse(result)
        self.assertEqual(
            self.account.calculate_balance().amount,
            Decimal('1000')
        )


class TransactionHistoryTest(TestCase):
    def setUp(self):
        self.account_id = AccountId(1)
        self.now = datetime.now()
        self.transaction1 = Transaction(
            id=None,
            source_account_id=self.account_id,
            target_account_id=AccountId(2),
            money=Money(Decimal('100')),
            timestamp=self.now,
            status="COMPLETED"
        )
        self.transaction2 = Transaction(
            id=None,
            source_account_id=AccountId(2),
            target_account_id=self.account_id,
            money=Money(Decimal('200')),
            timestamp=self.now,
            status="COMPLETED"
        )
        self.history = TransactionHistory(
            transactions=[self.transaction1, self.transaction2],
            account_id=self.account_id
        )

    def test_get_total_sent(self):
        """送金総額のテスト"""
        self.assertEqual(
            self.history.get_total_sent().amount,
            Decimal('100')
        )

    def test_get_total_received(self):
        """受取総額のテスト"""
        self.assertEqual(
            self.history.get_total_received().amount,
            Decimal('200')
        )

    def test_get_transactions_in_period(self):
        """期間指定での取引取得テスト"""
        start_date = self.now - timedelta(days=1)
        end_date = self.now + timedelta(days=1)
        transactions = self.history.get_transactions_in_period(
            start_date,
            end_date
        )
        self.assertEqual(len(transactions), 2)


class AccountLimitsTest(TestCase):
    def setUp(self):
        self.account_id = AccountId(1)
        self.daily_limit = DailyLimit(
            amount=Money(Decimal('1000')),
            used_amount=Money(Decimal('0')),
            reset_time=datetime.now() + timedelta(days=1)
        )
        self.limits = AccountLimits(
            account_id=self.account_id,
            daily_limit=self.daily_limit,
            minimum_balance=Money(Decimal('100')),
            maximum_balance=Money(Decimal('10000'))
        )

    def test_can_withdraw(self):
        """出金可能判定のテスト"""
        current_balance = Money(Decimal('500'))
        self.assertTrue(
            self.limits.can_withdraw(current_balance, Money(Decimal('300')))
        )
        self.assertFalse(
            self.limits.can_withdraw(current_balance, Money(Decimal('450')))
        )

    def test_can_deposit(self):
        """入金可能判定のテスト"""
        current_balance = Money(Decimal('9000'))
        self.assertTrue(
            self.limits.can_deposit(current_balance, Money(Decimal('500')))
        )
        self.assertFalse(
            self.limits.can_deposit(current_balance, Money(Decimal('1500')))
        ) 