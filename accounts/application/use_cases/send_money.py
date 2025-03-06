from dataclasses import dataclass
from datetime import datetime, timedelta

from accounts.application.ports.in_ports import SendMoneyCommand, SendMoneyUseCase
from accounts.application.ports.out_ports import (
    LoadAccountPort,
    UpdateAccountStatePort,
    AccountLockPort
)
from accounts.domain.value_objects import Money


@dataclass
class MoneyTransferProperties:
    maximum_transfer_threshold: Money = Money.of(1_000_000)


class SendMoneyService(SendMoneyUseCase):
    def __init__(
        self,
        load_account_port: LoadAccountPort,
        account_lock_port: AccountLockPort,
        update_account_state_port: UpdateAccountStatePort,
        money_transfer_properties: MoneyTransferProperties
    ):
        self._load_account_port = load_account_port
        self._account_lock_port = account_lock_port
        self._update_account_state_port = update_account_state_port
        self._money_transfer_properties = money_transfer_properties

    def send_money(self, command: SendMoneyCommand) -> bool:
        self._check_threshold(command)

        baseline_date = datetime.now() - timedelta(days=10)

        source_account = self._load_account_port.load_account(
            command.source_account_id,
            baseline_date
        )

        target_account = self._load_account_port.load_account(
            command.target_account_id,
            baseline_date
        )

        if source_account.id is None:
            raise ValueError("送金元アカウントIDが見つかりません")
        if target_account.id is None:
            raise ValueError("送金先アカウントIDが見つかりません")

        self._account_lock_port.lock_account(source_account.id)
        if not source_account.withdraw(command.money, target_account.id):
            self._account_lock_port.release_account(source_account.id)
            return False

        self._account_lock_port.lock_account(target_account.id)
        if not target_account.deposit(command.money, source_account.id):
            self._account_lock_port.release_account(source_account.id)
            self._account_lock_port.release_account(target_account.id)
            return False

        self._update_account_state_port.update_activities(source_account)
        self._update_account_state_port.update_activities(target_account)

        self._account_lock_port.release_account(source_account.id)
        self._account_lock_port.release_account(target_account.id)
        return True

    def _check_threshold(self, command: SendMoneyCommand) -> None:
        max_amount = self._money_transfer_properties.maximum_transfer_threshold
        if command.money.amount > max_amount.amount:
            raise ValueError(
                f"送金額が上限を超えています（上限: {max_amount.amount}円）"
            ) 