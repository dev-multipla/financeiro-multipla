
# financeiro/views.py
from rest_framework import viewsets, permissions
from .models import ContaFinanceira, CentroCusto
from .serializers import ContaFinanceiraSerializer, CentroCustoSerializer
from multipla_teste.core.mixins import CompanyScopedMixin

class ContaFinanceiraViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ContaFinanceira.objects.all()
    serializer_class = ContaFinanceiraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()  # já filtra por empresa_id
        return qs.filter(is_active=True).order_by('descricao')


class CentroCustoViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CentroCusto.objects.all()
    serializer_class = CentroCustoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()  # já filtra por empresa_id
        return qs.filter(is_active=True).order_by('descricao')
