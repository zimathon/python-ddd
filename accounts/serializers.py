from rest_framework import serializers
from .models import Account, Activity


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'owner_account', 'source_account', 'target_account', 'timestamp', 'amount']
        read_only_fields = ['timestamp']


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        source='calculate_balance'
    )

    class Meta:
        model = Account
        fields = ['id', 'created_at', 'updated_at', 'balance']
        read_only_fields = ['created_at', 'updated_at'] 