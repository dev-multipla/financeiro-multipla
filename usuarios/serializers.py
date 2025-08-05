from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PerfilUsuario, UsuarioEmpresaRole
from empresas.models import Empresa
from empresas.serializers import EmpresaSerializer


class UsuarioEmpresaRoleSerializer(serializers.ModelSerializer):
    """Serializer para gerenciar papéis de usuário por empresa."""
    empresa = serializers.PrimaryKeyRelatedField(queryset=Empresa.objects.all())
    role = serializers.ChoiceField(choices=UsuarioEmpresaRole.ROLE_CHOICES)

    class Meta:
        model = UsuarioEmpresaRole
        fields = ['empresa', 'role']


class PerfilUsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de perfil de usuário com papéis por empresa."""
    empresas_acessiveis = UsuarioEmpresaRoleSerializer(many=True, required=False)

    class Meta:
        model = PerfilUsuario
        fields = ['email', 'empresa_padrao', 'empresas_acessiveis']

    def create(self, validated_data):
        # Extraímos a lista de papéis
        empresas_roles_data = validated_data.pop('empresas_acessiveis', [])
        perfil = PerfilUsuario.objects.create(**validated_data)
        
        # Criamos cada instância de UsuarioEmpresaRole
        for er in empresas_roles_data:
            UsuarioEmpresaRole.objects.create(
                perfil_usuario=perfil,
                empresa=er['empresa'],
                role=er['role']
            )
        return perfil

    def update(self, instance, validated_data):
        empresas_roles_data = validated_data.pop('empresas_acessiveis', None)
        instance = super().update(instance, validated_data)
        
        if empresas_roles_data is not None:
            # Remove papéis existentes e cria os novos
            UsuarioEmpresaRole.objects.filter(perfil_usuario=instance).delete()
            for er in empresas_roles_data:
                UsuarioEmpresaRole.objects.create(
                    perfil_usuario=instance,
                    empresa=er['empresa'],
                    role=er['role']
                )
        return instance


class PerfilUsuarioDetailSerializer(serializers.ModelSerializer):
    """Serializer para exibição detalhada do perfil com empresas e papéis."""
    empresa_roles = serializers.SerializerMethodField()
    empresa_padrao = EmpresaSerializer(read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = ['email', 'empresa_padrao', 'empresa_roles']

    def get_empresa_roles(self, obj):
        """Retorna lista de empresas com seus respectivos papéis."""
        queryset = UsuarioEmpresaRole.objects.filter(perfil_usuario=obj)
        return [
            {
                "empresa": EmpresaSerializer(ur.empresa).data,
                "role": ur.role
            }
            for ur in queryset
        ]


class PerfilUsuarioNestedSerializer(serializers.ModelSerializer):
    """Serializer aninhado simples para atualizações de perfil."""
    empresas_acessiveis = serializers.PrimaryKeyRelatedField(
        queryset=Empresa.objects.all(),
        many=True,
        required=False
    )
    empresa_padrao = serializers.PrimaryKeyRelatedField(
        queryset=Empresa.objects.all()
    )

    class Meta:
        model = PerfilUsuario
        fields = ['email', 'empresa_padrao', 'empresas_acessiveis']

    def update(self, instance, validated_data):
        # Extrai o M2M se vier
        empresas = validated_data.pop('empresas_acessiveis', None)
        # Extrai a FK padrão se vier
        padrao = validated_data.pop('empresa_padrao', None)

        # Atualiza campos simples
        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        # Atualiza empresa padrão se fornecida
        if padrao is not None:
            instance.empresa_padrao = padrao

        instance.save()

        # Atualiza empresas acessíveis se fornecidas
        if empresas is not None:
            instance.empresas_acessiveis.set(empresas)

        return instance


class UserSerializer(serializers.ModelSerializer):
    """Serializer para criação de usuários com perfil completo."""
    email = serializers.EmailField(write_only=True)
    perfilusuario = PerfilUsuarioCreateSerializer()
    is_staff = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'perfilusuario', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Já existe usuário com este e-mail.")
        return value

    def create(self, validated_data):
        print("Dados validados no serializer:", validated_data)
        
        is_staff = validated_data.pop('is_staff', False)
        email = validated_data.pop('email')
        perfil_data = validated_data.pop('perfilusuario')
        password = validated_data.pop('password')

        # Cria o usuário
        user = User(username=validated_data['username'], email=email)
        user.is_staff = is_staff
        user.set_password(password)
        user.save()

        # Cria o perfil
        perfil = PerfilUsuario.objects.create(
            user=user,
            email=email,
            empresa_padrao=perfil_data['empresa_padrao']
        )

        # Cria os papéis por empresa se fornecidos
        empresas_roles_data = perfil_data.get('empresas_acessiveis', [])
        for er in empresas_roles_data:
            UsuarioEmpresaRole.objects.create(
                perfil_usuario=perfil,
                empresa=er['empresa'],
                role=er['role']
            )
        
        return user

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfilusuario', None)
        is_staff = validated_data.pop('is_staff', None)
        new_email = validated_data.pop('email', None)

        # Atualiza campos do usuário
        if is_staff is not None:
            instance.is_staff = is_staff
        if new_email:
            if User.objects.filter(email=new_email).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("E-mail já em uso.")
            instance.email = new_email

        instance = super().update(instance, validated_data)

        # Atualiza o perfil se fornecido
        if perfil_data:
            perfil = instance.perfilusuario
            if new_email:
                perfil.email = new_email
            
            padrao = perfil_data.get('empresa_padrao')
            if padrao:
                perfil.empresa_padrao = padrao

            # Atualiza papéis por empresa
            empresas_roles_data = perfil_data.get('empresas_acessiveis', None)
            if empresas_roles_data is not None:
                UsuarioEmpresaRole.objects.filter(perfil_usuario=perfil).delete()
                for er in empresas_roles_data:
                    UsuarioEmpresaRole.objects.create(
                        perfil_usuario=perfil,
                        empresa=er['empresa'],
                        role=er['role']
                    )
            
            perfil.save()

        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer para exibição detalhada de usuários."""
    perfilusuario = PerfilUsuarioDetailSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'perfilusuario']

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfilusuario', None)
        instance = super().update(instance, validated_data)
        
        if perfil_data:
            perfil_serializer = self.fields['perfilusuario']
            perfil_serializer.update(instance.perfilusuario, perfil_data)
        
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para tokens JWT.
    Ao gerar o access+refresh, também injeta dados de empresa.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Aqui poderia adicionar claims customizadas se necessário
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Adiciona dados do usuário e empresas à resposta
        try:
            perfil = self.user.perfilusuario
            
            # Serializa empresa padrão e empresas acessíveis
            empresa_padrao = EmpresaSerializer(perfil.empresa_padrao).data
            empresas_acessiveis = EmpresaSerializer(
                perfil.empresas_acessiveis.all(), many=True
            ).data

            # Adiciona dados extras à resposta
            data.update({
                'user_id': self.user.id,
                'username': self.user.username,
                'empresa_padrao': empresa_padrao,
                'empresas_acessiveis': empresas_acessiveis
            })
            
        except PerfilUsuario.DoesNotExist:
            # Caso o usuário não tenha perfil, retorna apenas os tokens
            pass

        return data