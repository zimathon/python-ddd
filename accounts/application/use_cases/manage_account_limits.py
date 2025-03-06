from accounts.application.ports.in_ports import (
    UpdateAccountLimitsCommand,
    UpdateAccountLimitsUseCase,
    GetAccountLimitsUseCase
)
from accounts.application.ports.out_ports import (
    LoadAccountLimitsPort,
    UpdateAccountLimitsPort
)
from accounts.domain.models import AccountLimits, AccountId


class ManageAccountLimitsService(UpdateAccountLimitsUseCase, GetAccountLimitsUseCase):
    def __init__(
        self,
        load_account_limits_port: LoadAccountLimitsPort,
        update_account_limits_port: UpdateAccountLimitsPort
    ):
        self._load_account_limits_port = load_account_limits_port
        self._update_account_limits_port = update_account_limits_port

    def update_limits(
        self,
        command: UpdateAccountLimitsCommand
    ) -> AccountLimits:
        current_limits = self._load_account_limits_port.load_account_limits(
            command.account_id
        )

        if command.daily_limit:
            current_limits.daily_limit.amount = command.daily_limit

        if command.minimum_balance:
            current_limits.minimum_balance = command.minimum_balance

        if command.maximum_balance:
            current_limits.maximum_balance = command.maximum_balance

        self._update_account_limits_port.update_account_limits(current_limits)
        return current_limits

    def get_limits(self, account_id: AccountId) -> AccountLimits:
        return self._load_account_limits_port.load_account_limits(account_id) 