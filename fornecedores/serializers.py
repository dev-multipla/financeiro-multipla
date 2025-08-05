from rest_framework import serializers
from .models import Fornecedor

class FornecedorSerializer(serializers.ModelSerializer):
    cpf_cnpj = serializers.CharField(required=False, allow_blank=True, allow_null=True) 
    cep = serializers.CharField(required=False, allow_blank=True, allow_null=True) 
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    class Meta:
        model = Fornecedor
        fields = '__all__'  # Inclui todos os campos do modelo
#fornecedores/serializers.py
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Fornecedor

class FornecedorSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    cpf_cnpj = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            UniqueValidator(queryset=Fornecedor.objects.all(), message="Este CPF/CNPJ já está em uso.")
        ]
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            UniqueValidator(queryset=Fornecedor.objects.all(), message="Este email já está em uso.")
        ]
    )
    cep = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Fornecedor
        fields = '__all__'
    
    def validate_email(self, value):
        if value == '':
            return None
        return value

class FornecedorSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ['id', 'nome']  

class FornecedorListSerializer(serializers.ModelSerializer):
    cpf_cnpj = serializers.CharField(required=False, allow_blank=True)
    cep = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    class Meta:
        model = Fornecedor
        fields = '__all__'
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Fornecedor
        # Inclua explicitamente 'empresa' junto com os outros campos
        fields = ['id', 'nome', 'empresa']

class FornecedorListSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    cpf_cnpj = serializers.CharField(required=False, allow_blank=True)
    cep = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    
    class Meta:
        model = Fornecedor
        fields = '__all__'
