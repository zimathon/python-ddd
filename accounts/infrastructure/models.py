from django.db import models


class AccountModel(models.Model):
    """
    口座を表すデータベースモデル
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    minimum_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_balance = models.DecimalField(max_digits=10, decimal_places=2, default=1_000_000_000)

    class Meta:
        db_table = 'account'


class ActivityModel(models.Model):
    """
    取引活動を表すデータベースモデル
    """
    owner_account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='owned_activities'
    )
    source_account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='source_activities'
    )
    target_account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='target_activities'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'activity'
        ordering = ['-timestamp']


class TransactionModel(models.Model):
    """取引を表すデータベースモデル"""
    source_account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='source_transactions'
    )
    target_account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='target_transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'transaction'
        ordering = ['-timestamp']


class DailyLimitModel(models.Model):
    """1日あたりの取引制限を表すデータベースモデル"""
    account = models.OneToOneField(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='daily_limit'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reset_time = models.DateTimeField()

    class Meta:
        db_table = 'daily_limit'


class AccountStatementModel(models.Model):
    """取引明細を表すデータベースモデル"""
    account = models.ForeignKey(
        AccountModel,
        on_delete=models.CASCADE,
        related_name='statements'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'account_statement'
        ordering = ['-end_date'] 