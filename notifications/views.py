# notifications/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import NotificacaoVencimento
from notifications.serializers import NotificacaoVencimentoSerializer
from multipla_teste.core.mixins import CompanyScopedMixin
from django.contrib.auth.models import User
from multipla_teste.tenant_utils import default_db_context

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para notificações que funciona com multi-tenant.
    Não usa CompanyScopedMixin porque as notificações são filtradas por usuário,
    e o tenant routing já garante isolamento por empresa.
    """
    serializer_class = NotificacaoVencimentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # O tenant routing já garante que estamos no banco correto
        # Filtramos apenas por usuário
        return NotificacaoVencimento.objects.filter(
            usuario=self.request.user
        ).select_related('projecao', 'projecao__contrato')

    @action(detail=False, methods=['get'])
    def nao_lidas(self, request):
        """Retorna contagem de notificações não lidas"""
        count = self.get_queryset().filter(lida=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        """Retorna resumo das notificações"""
        qs = self.get_queryset()
        
        resumo = {
            'total': qs.count(),
            'nao_lidas': qs.filter(lida=False).count(),
            'por_tipo': {}
        }
        
        # Conta por tipo
        for tipo, nome in NotificacaoVencimento.TIPOS:
            resumo['por_tipo'][tipo] = qs.filter(tipo=tipo, lida=False).count()
        
        return Response(resumo)

    @action(detail=True, methods=['post'])
    def marcar_lida(self, request, pk=None):
        """Marca uma notificação como lida"""
        notificacao = self.get_object()
        notificacao.lida = True
        notificacao.save()
        return Response({'status': 'lida'})

    @action(detail=False, methods=['post'])
    def marcar_todas_lidas(self, request):
        """Marca todas as notificações do usuário como lidas"""
        count = self.get_queryset().filter(lida=False).update(lida=True)
        return Response({'marcadas': count})

    def perform_create(self, serializer):
        # Sempre associa ao usuário logado
        serializer.save(usuario=self.request.user)