from rest_framework import serializers

from accounts.domain.models import AccountId, Transaction, TransactionHistory
from accounts.domain.value_objects import Money
from accounts.infrastructure.models import AccountModel, ActivityModel


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityModel
        fields = ['id', 'owner_account', 'source_account', 'target_account', 'timestamp', 'amount']
        read_only_fields = ['timestamp']


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = AccountModel
        fields = ['id', 'created_at', 'updated_at', 'balance']
        read_only_fields = ['created_at', 'updated_at', 'balance']

    def get_balance(self, obj):
        from accounts.application.use_cases.get_account_balance import GetAccountBalanceService
        from accounts.infrastructure.repositories import DjangoAccountRepository
        
        service = GetAccountBalanceService(DjangoAccountRepository())
        balance = service.get_account_balance(
            query=GetAccountBalanceQuery(account_id=AccountId(obj.id))
        )
        return str(balance.amount)


class SendMoneyRequestSerializer(serializers.Serializer):
    target_account_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError("送金額は0より大きい必要があります")
        return data


class TransactionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    source_account_id = serializers.IntegerField()
    target_account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    timestamp = serializers.DateTimeField()
    status = serializers.CharField()


class TransactionHistorySerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    transactions = TransactionSerializer(many=True)
    total_sent = serializers.SerializerMethodField()
    total_received = serializers.SerializerMethodField()

    def get_total_sent(self, obj):
        return str(obj.get_total_sent().amount)

    def get_total_received(self, obj):
        return str(obj.get_total_received().amount)


class AccountStatementSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    opening_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    transactions = TransactionSerializer(many=True)


class AccountLimitsSerializer(serializers.Serializer):
    daily_limit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    minimum_balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    maximum_balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    used_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True) 