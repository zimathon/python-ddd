from accounts.application.ports.in_ports import (
    GenerateAccountStatementCommand,
    GenerateAccountStatementUseCase
)
from accounts.application.ports.out_ports import (
    LoadAccountPort,
    LoadTransactionHistoryPort,
    SaveAccountStatementPort
)
from accounts.domain.models import AccountStatement


class GenerateAccountStatementService(GenerateAccountStatementUseCase):
    def __init__(
        self,
        load_account_port: LoadAccountPort,
        load_transaction_history_port: LoadTransactionHistoryPort,
        save_account_statement_port: SaveAccountStatementPort
    ):
        self._load_account_port = load_account_port
        self._load_transaction_history_port = load_transaction_history_port
        self._save_account_statement_port = save_account_statement_port

    def generate_statement(
        self,
        command: GenerateAccountStatementCommand
    ) -> AccountStatement:
        account = self._load_account_port.load_account(
            command.account_id,
            command.period.start_date
        )
        
        transaction_history = self._load_transaction_history_port.load_transaction_history(
            command.account_id
        )

        statement = AccountStatement.create_for_account(
            account_id=command.account_id,
            period=command.period,
            transaction_history=transaction_history,
            opening_balance=account.calculate_balance()
        )

        self._save_account_statement_port.save_account_statement(statement)
        return statement 