from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from accounts.domain.models import (
    AccountId, Money, TransactionHistory,
    AccountStatement, StatementPeriod,
    TransactionSummary, AccountLimits
)


@dataclass
class SendMoneyCommand:
    source_account_id: AccountId
    target_account_id: AccountId
    money: Money

    def __post_init__(self):
        if not self.money.is_positive_or_zero():
            raise ValueError("送金額は0以上である必要があります")
        if not all([self.source_account_id, self.target_account_id]):
            raise ValueError("送金元と送金先のアカウントIDは必須です")


class SendMoneyUseCase(ABC):
    @abstractmethod
    def send_money(self, command: SendMoneyCommand) -> bool:
        pass


@dataclass
class GetAccountBalanceQuery:
    account_id: AccountId
    baseline_date: Optional[datetime] = None


class GetAccountBalanceUseCase(ABC):
    @abstractmethod
    def get_account_balance(self, query: GetAccountBalanceQuery) -> Money:
        pass


@dataclass
class GetTransactionHistoryQuery:
    account_id: AccountId
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class GetTransactionHistoryUseCase(ABC):
    @abstractmethod
    def get_transaction_history(
        self,
        query: GetTransactionHistoryQuery
    ) -> TransactionHistory:
        pass


@dataclass
class GetTransactionSummaryQuery:
    account_id: AccountId
    period: StatementPeriod


class GetTransactionSummaryUseCase(ABC):
    @abstractmethod
    def get_transaction_summary(
        self,
        query: GetTransactionSummaryQuery
    ) -> TransactionSummary:
        pass


@dataclass
class GenerateAccountStatementCommand:
    account_id: AccountId
    period: StatementPeriod


class GenerateAccountStatementUseCase(ABC):
    @abstractmethod
    def generate_statement(
        self,
        command: GenerateAccountStatementCommand
    ) -> AccountStatement:
        pass


@dataclass
class UpdateAccountLimitsCommand:
    account_id: AccountId
    daily_limit: Optional[Money] = None
    minimum_balance: Optional[Money] = None
    maximum_balance: Optional[Money] = None


class UpdateAccountLimitsUseCase(ABC):
    @abstractmethod
    def update_limits(
        self,
        command: UpdateAccountLimitsCommand
    ) -> AccountLimits:
        pass


class GetAccountLimitsUseCase(ABC):
    @abstractmethod
    def get_limits(self, account_id: AccountId) -> AccountLimits:
        pass 