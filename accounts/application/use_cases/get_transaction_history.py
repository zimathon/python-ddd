from accounts.application.ports.in_ports import (
    GetTransactionHistoryQuery,
    GetTransactionHistoryUseCase
)
from accounts.application.ports.out_ports import LoadTransactionHistoryPort
from accounts.domain.models import TransactionHistory


class GetTransactionHistoryService(GetTransactionHistoryUseCase):
    def __init__(self, load_transaction_history_port: LoadTransactionHistoryPort):
        self._load_transaction_history_port = load_transaction_history_port

    def get_transaction_history(
        self,
        query: GetTransactionHistoryQuery
    ) -> TransactionHistory:
        history = self._load_transaction_history_port.load_transaction_history(
            query.account_id
        )
        
        if query.start_date and query.end_date:
            filtered_transactions = history.get_transactions_in_period(
                query.start_date,
                query.end_date
            )
            history.transactions = filtered_transactions
        
        return history 