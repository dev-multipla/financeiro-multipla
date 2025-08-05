#projetos/serializers.py
from rest_framework import serializers
from .models import Projeto

class ProjetoSerializer(serializers.ModelSerializer):
    prazo_indeterminado = serializers.ReadOnlyField()
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Projeto
        fields = '__all__'

class ProjetoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projeto
        fields = '__all__'
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Projeto
        fields = '__all__'
        
class ProjetoSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projeto
        fields = ['id', 'nome']
