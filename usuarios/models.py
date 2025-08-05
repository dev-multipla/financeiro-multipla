from django.db import models
from django.contrib.auth.models import User
from empresas.models import Empresa


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    empresa_padrao = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        help_text="Empresa padrão"
    )
    # Relação ManyToMany simples para empresas acessíveis
    empresas_acessiveis = models.ManyToManyField(Empresa, related_name='usuarios', blank=True)

    def __str__(self):
        return self.user.username


class UsuarioEmpresaRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('financeiro', 'Financeiro'),
        ('leitura', 'Somente Leitura')
    ]

    perfil_usuario = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='leitura')

    class Meta:
        unique_together = ('perfil_usuario', 'empresa')
        verbose_name = "Papel de Usuário por Empresa"
        verbose_name_plural = "Papéis de Usuários por Empresa"

    def __str__(self):
        return f"{self.perfil_usuario.user.username} em {self.empresa.nome} como {self.role}"
