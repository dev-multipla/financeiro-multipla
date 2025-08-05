#relatorios/serializers.py
from rest_framework import serializers


class RelatorioResultadoContratoSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    data_movimento = serializers.DateField()
    contrato = serializers.CharField()
    centro_custo = serializers.CharField(allow_blank=True)
    conta_financeira = serializers.CharField(allow_blank=True)
    valor = serializers.DecimalField(max_digits=14, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=14, decimal_places=2)
    
class RelatorioResultadoProjetoSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    data_movimento = serializers.DateField()
    projeto = serializers.CharField()
    contrato = serializers.CharField()
    centro_custo = serializers.CharField(allow_blank=True)
    conta_financeira = serializers.CharField(allow_blank=True)
    valor = serializers.DecimalField(max_digits=14, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=14, decimal_places=2)