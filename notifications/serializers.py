# notifications/serializers.py
from rest_framework import serializers
from notifications.models import NotificacaoVencimento

class NotificacaoVencimentoSerializer(serializers.ModelSerializer):
    contrato_info = serializers.SerializerMethodField()
    tempo_relativo = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificacaoVencimento
        fields = [
            'id', 'tipo', 'titulo', 'mensagem', 'lida', 'created_at',
            'contrato_info', 'tempo_relativo'
        ]
        read_only_fields = ['id', 'created_at', 'usuario']
    
    def get_contrato_info(self, obj):
        if obj.projecao and obj.projecao.contrato:
            contrato = obj.projecao.contrato
            return {
                'numero': contrato.numero,
                'descricao': contrato.descricao,
                'valor_parcela': obj.projecao.valor_parcela,
                'data_vencimento': obj.projecao.data_vencimento
            }
        return None
    
    def get_tempo_relativo(self, obj):
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"há {diff.days} dia{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"há {hours} hora{'s' if hours > 1 else ''}"
        else:
            minutes = diff.seconds // 60
            return f"há {minutes} minuto{'s' if minutes > 1 else ''}"