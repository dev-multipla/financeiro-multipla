from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Funcionario, SEXO_CHOICES, ESTADO_CIVIL_CHOICES, GRAU_INSTRUCAO_CHOICES, TIPO_CONTRATO_CHOICES, CATEGORIA_CHOICES, FORMA_PAGAMENTO_CHOICES

class FuncionarioSerializer(serializers.ModelSerializer):
    cpf = serializers.CharField(
        validators=[UniqueValidator(queryset=Funcionario.objects.all(), message="CPF já cadastrado")]
    )
    matricula = serializers.CharField(
        validators=[UniqueValidator(queryset=Funcionario.objects.all(), message="Matrícula já existe")]
    )
    
    sexo = serializers.ChoiceField(choices=SEXO_CHOICES)
    estado_civil = serializers.ChoiceField(choices=ESTADO_CIVIL_CHOICES)
    grau_instrucao = serializers.ChoiceField(choices=GRAU_INSTRUCAO_CHOICES)
    tipo_contrato = serializers.ChoiceField(choices=TIPO_CONTRATO_CHOICES)
    categoria = serializers.ChoiceField(choices=CATEGORIA_CHOICES)
    forma_pagamento = serializers.ChoiceField(choices=FORMA_PAGAMENTO_CHOICES)
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Funcionario
        fields = '__all__'
        extra_kwargs = {
            'salario': {'min_value': 0},
            'data_nascimento': {'format': '%d/%m/%Y'},
            'data_admissao': {'format': '%d/%m/%Y'},
            'cep': {
                'error_messages': {'blank': 'O CEP é obrigatório.'},
                'required': False,
                'allow_null': True
            },
            'endereco': {'required': True},
            'cidade': {'required': True},
            'estado': {'required': True}
        }
    def validate(self, data):
        # Validações adicionais personalizadas podem ser adicionadas aqui
        if data.get('data_nascimento') and data.get('data_admissao'):
            if data['data_admissao'] < data['data_nascimento']:
                raise serializers.ValidationError("Data de admissão não pode ser anterior à data de nascimento")
        return data

class FuncionarioSelectSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Funcionario
        fields = ['id', 'nome_completo', 'matricula']

class FuncionarioListSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Funcionario
        fields = ['id', 'nome_completo', 'cargo_funcao', 'matricula', 'data_admissao']