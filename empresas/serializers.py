#empresas/serializers.pý
from rest_framework import serializers
from .models import Empresa, Filial

class FilialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filial
        fields = '__all__'

class EmpresaSerializer(serializers.ModelSerializer):
    filiais = FilialSerializer(many=True, read_only=True)  # Relacionamento com as filiais

    class Meta:
        model = Empresa
        fields = '__all__'


class EmpresaListSerializer(serializers.ModelSerializer):
    """Serializer para listar empresas com informações básicas."""

    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'cnpj']  # Adicione outros campos conforme necessário


class FilialListSerializer(serializers.ModelSerializer):
    """Serializer para listar filiais com informações básicas."""

    class Meta:
        model = Filial
        fields = ['id', 'nome', 'empresa']  # Adicione outros campos conforme necessário
