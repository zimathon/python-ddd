from django.db import models
from decimal import Decimal


class Account(models.Model):
    """
    口座を表すモデル。
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account'

    def calculate_balance(self, baseline_date=None):
        """
        口座の残高を計算する。
        baseline_dateが指定された場合、その日付以降の取引のみを考慮する。
        """
        activities = self.owned_activities.all()
        if baseline_date:
            activities = activities.filter(timestamp__gte=baseline_date)

        deposit_balance = sum(
            activity.amount
            for activity in activities
            if activity.target_account_id == self.id
        )
        withdrawal_balance = sum(
            activity.amount
            for activity in activities
            if activity.source_account_id == self.id
        )
        return Decimal(deposit_balance - withdrawal_balance)

    def withdraw(self, amount: Decimal, target_account_id: int) -> bool:
        """
        指定された金額を引き出す。
        引き出しが成功した場合はTrue、失敗した場合はFalseを返す。
        """
        if not self._may_withdraw(amount):
            return False

        Activity.objects.create(
            owner_account=self,
            source_account_id=self.id,
            target_account_id=target_account_id,
            amount=amount
        )
        return True

    def deposit(self, amount: Decimal, source_account_id: int) -> bool:
        """
        指定された金額を預け入れる。
        """
        Activity.objects.create(
            owner_account=self,
            source_account_id=source_account_id,
            target_account_id=self.id,
            amount=amount
        )
        return True

    def _may_withdraw(self, amount: Decimal) -> bool:
        """
        引き出し可能かどうかを判断する。
        """
        return (self.calculate_balance() - amount) >= 0


class Activity(models.Model):
    """
    口座間の取引活動を表すモデル。
    """
    owner_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='owned_activities'
    )
    source_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='source_activities'
    )
    target_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='target_activities'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'activity'
        ordering = ['-timestamp'] 