from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from accounts.application.ports.in_ports import (
    SendMoneyCommand,
    GetTransactionHistoryQuery,
    GenerateAccountStatementCommand,
    UpdateAccountLimitsCommand
)
from accounts.application.use_cases.send_money import SendMoneyService, MoneyTransferProperties
from accounts.application.use_cases.get_transaction_history import GetTransactionHistoryService
from accounts.application.use_cases.generate_statement import GenerateAccountStatementService
from accounts.application.use_cases.manage_account_limits import ManageAccountLimitsService
from accounts.domain.models import AccountId, StatementPeriod
from accounts.domain.value_objects import Money
from accounts.infrastructure.models import AccountModel, ActivityModel
from accounts.infrastructure.repositories import DjangoAccountRepository, NoOpAccountLock
from .serializers import (
    AccountSerializer, ActivitySerializer, SendMoneyRequestSerializer,
    TransactionHistorySerializer, AccountStatementSerializer,
    AccountLimitsSerializer
)


class AccountViewSet(viewsets.ModelViewSet):
    """口座を管理するViewSet"""
    queryset = AccountModel.objects.all()
    serializer_class = AccountSerializer

    @extend_schema(
        request=SendMoneyRequestSerializer,
        responses={200: dict, 400: dict},
        description="指定された口座から別の口座に送金を行います",
        examples=[
            OpenApiExample(
                'Success Response',
                value={'status': '送金が完了しました'},
                status_codes=['200']
            ),
            OpenApiExample(
                'Error Response',
                value={'error': '残高が不足しています'},
                status_codes=['400']
            ),
        ]
    )
    @action(detail=True, methods=['post'])
    def send_money(self, request, pk=None):
        """送金処理を行うエンドポイント"""
        serializer = SendMoneyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        repository = DjangoAccountRepository()
        service = SendMoneyService(
            load_account_port=repository,
            account_lock_port=NoOpAccountLock(),
            update_account_state_port=repository,
            money_transfer_properties=MoneyTransferProperties()
        )

        command = SendMoneyCommand(
            source_account_id=AccountId(int(pk)),
            target_account_id=AccountId(serializer.validated_data['target_account_id']),
            money=Money(serializer.validated_data['amount'])
        )

        try:
            if service.send_money(command):
                return Response({'status': '送金が完了しました'})
            return Response(
                {'error': '送金に失敗しました'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='取引履歴の開始日（YYYY-MM-DD）'
            ),
            OpenApiParameter(
                name='end_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='取引履歴の終了日（YYYY-MM-DD）'
            ),
        ],
        responses={200: TransactionHistorySerializer},
        description="指定された期間の取引履歴を取得します"
    )
    @action(detail=True, methods=['get'])
    def transaction_history(self, request, pk=None):
        """取引履歴を取得するエンドポイント"""
        repository = DjangoAccountRepository()
        service = GetTransactionHistoryService(repository)

        query = GetTransactionHistoryQuery(
            account_id=AccountId(int(pk)),
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date')
        )

        history = service.get_transaction_history(query)
        serializer = TransactionHistorySerializer(history)
        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses={200: AccountStatementSerializer},
        description="口座の取引明細書を生成します"
    )
    @action(detail=True, methods=['post'])
    def generate_statement(self, request, pk=None):
        """取引明細書を生成するエンドポイント"""
        repository = DjangoAccountRepository()
        service = GenerateAccountStatementService(
            load_account_port=repository,
            load_transaction_history_port=repository,
            save_account_statement_port=repository
        )

        period = StatementPeriod(
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date')
        )

        command = GenerateAccountStatementCommand(
            account_id=AccountId(int(pk)),
            period=period
        )

        statement = service.generate_statement(command)
        serializer = AccountStatementSerializer(statement)
        return Response(serializer.data)

    @extend_schema(
        request=AccountLimitsSerializer,
        responses={200: AccountLimitsSerializer},
        description="口座の取引制限を更新します"
    )
    @action(detail=True, methods=['put'])
    def update_limits(self, request, pk=None):
        """取引制限を更新するエンドポイント"""
        serializer = AccountLimitsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        repository = DjangoAccountRepository()
        service = ManageAccountLimitsService(
            load_account_limits_port=repository,
            update_account_limits_port=repository
        )

        command = UpdateAccountLimitsCommand(
            account_id=AccountId(int(pk)),
            daily_limit=Money(serializer.validated_data.get('daily_limit')),
            minimum_balance=Money(serializer.validated_data.get('minimum_balance')),
            maximum_balance=Money(serializer.validated_data.get('maximum_balance'))
        )

        limits = service.update_limits(command)
        response_serializer = AccountLimitsSerializer(limits)
        return Response(response_serializer.data)


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """取引活動を表示するViewSet"""
    serializer_class = ActivitySerializer

    def get_queryset(self):
        """アカウントに関連する取引履歴を取得"""
        account_id = self.kwargs.get('account_pk')
        return ActivityModel.objects.filter(owner_account_id=account_id) 