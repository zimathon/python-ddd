from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

from accounts.domain.models import (
    Account, AccountId, Transaction, TransactionHistory,
    AccountStatement, StatementPeriod, AccountLimits
)


class LoadAccountPort(ABC):
    @abstractmethod
    def load_account(self, account_id: AccountId, baseline_date: datetime) -> Account:
        pass


class UpdateAccountStatePort(ABC):
    @abstractmethod
    def update_activities(self, account: Account) -> None:
        pass


class AccountLockPort(ABC):
    @abstractmethod
    def lock_account(self, account_id: AccountId) -> None:
        pass

    @abstractmethod
    def release_account(self, account_id: AccountId) -> None:
        pass


class LoadTransactionHistoryPort(ABC):
    @abstractmethod
    def load_transaction_history(self, account_id: AccountId) -> TransactionHistory:
        pass


class SaveTransactionPort(ABC):
    @abstractmethod
    def save_transaction(self, transaction: Transaction) -> None:
        pass


class LoadAccountLimitsPort(ABC):
    @abstractmethod
    def load_account_limits(self, account_id: AccountId) -> AccountLimits:
        pass


class UpdateAccountLimitsPort(ABC):
    @abstractmethod
    def update_account_limits(self, account_limits: AccountLimits) -> None:
        pass


class SaveAccountStatementPort(ABC):
    @abstractmethod
    def save_account_statement(self, statement: AccountStatement) -> None:
        pass


class LoadAccountStatementsPort(ABC):
    @abstractmethod
    def load_account_statements(
        self,
        account_id: AccountId,
        period: StatementPeriod
    ) -> List[AccountStatement]:
        pass 