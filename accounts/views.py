from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Account, Activity
from .serializers import AccountSerializer, ActivitySerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    @action(detail=True, methods=['post'])
    def send_money(self, request, pk=None):
        """
        送金処理を行うエンドポイント
        """
        source_account = self.get_object()
        target_account_id = request.data.get('target_account_id')
        amount = request.data.get('amount')

        if not all([target_account_id, amount]):
            return Response(
                {'error': '送金先アカウントIDと金額は必須です'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_account = Account.objects.get(id=target_account_id)
        except Account.DoesNotExist:
            return Response(
                {'error': '送金先アカウントが存在しません'},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            if source_account.withdraw(amount, target_account.id):
                target_account.deposit(amount, source_account.id)
                return Response({'status': '送金が完了しました'})
            return Response(
                {'error': '残高が不足しています'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        """
        アカウントに関連する取引履歴を取得
        """
        account_id = self.kwargs.get('account_pk')
        return Activity.objects.filter(owner_account_id=account_id) 