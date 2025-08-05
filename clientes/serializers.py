from rest_framework import serializers
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    cpf_cnpj = serializers.CharField(required=False, allow_blank=True)
    cep = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    class Meta:
        model = Cliente
        fields = '__all__'

class ClienteSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nome'] 

class ClientListSerializer(serializers.ModelSerializer):
    cpf_cnpj = serializers.CharField(required=False, allow_blank=True)
    cep = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    class Meta:
        model = Cliente
        fields = '__all__'
from rest_framework.validators import UniqueValidator
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    cpf_cnpj = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[
            UniqueValidator(queryset=Cliente.objects.all(), message="Este CPF/CNPJ já está em uso.")
        ]
    )
    cep = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            UniqueValidator(queryset=Cliente.objects.all(), message="Este email já está em uso.")
        ]
    )
    
    class Meta:
        model = Cliente
        fields = '__all__'
    
    def validate_email(self, value):
        if value == '':
            return None
        return value

class ClienteSelectSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'empresa']

class ClientListSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    cpf_cnpj = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[
            UniqueValidator(queryset=Cliente.objects.all(), message="Este CPF/CNPJ já está em uso.")
        ]
    )
    cep = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            UniqueValidator(queryset=Cliente.objects.all(), message="Este email já está em uso.")
        ]
    )
    
    class Meta:
        model = Cliente
        fields = '__all__'
