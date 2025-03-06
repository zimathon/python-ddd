from datetime import datetime

from accounts.application.ports.in_ports import (
    GetAccountBalanceQuery,
    GetAccountBalanceUseCase
)
from accounts.application.ports.out_ports import LoadAccountPort
from accounts.domain.value_objects import Money


class GetAccountBalanceService(GetAccountBalanceUseCase):
    def __init__(self, load_account_port: LoadAccountPort):
        self._load_account_port = load_account_port

    def get_account_balance(self, query: GetAccountBalanceQuery) -> Money:
        baseline_date = query.baseline_date or datetime.now()
        account = self._load_account_port.load_account(
            query.account_id,
            baseline_date
        )
        return account.calculate_balance() 