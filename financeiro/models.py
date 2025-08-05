# financeiro/models.py
from multipla_teste.tenant_router import get_current_tenant
from django.db import models
from django.core.validators import RegexValidator
from empresas.models import Empresa

class ContaFinanceira(models.Model):
    mascara_conta = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d\.\d{2}\.\d{3}\.\d{4}$',
                message='A máscara deve seguir o formato 1.11.111.1111'
            )
        ]
    )
    descricao = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        """Soft-delete: apenas marca como inativo"""
        self.is_active = False
        self.save() 

class CentroCusto(models.Model):
    id = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=100, blank=False, null=False)
    mascara_centro_custo = models.CharField(max_length=3, unique=True)
    is_active = models.BooleanField(default=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        db_index=True,
        db_constraint=False,   
    )

    class Meta:
        # agora cada empresa pode ter sua própria sequência de máscaras
        unique_together = (('empresa', 'mascara_conta'),)
        verbose_name = 'Conta Financeira'
        verbose_name_plural = 'Contas Financeiras'

    def delete(self, *args, **kwargs):
        """Soft-delete: apenas marca como inativo"""
        self.is_active = False
        self.save()

    def save(self, *args, **kwargs):
        if not self.mascara_centro_custo:
            # Gera a máscara de forma sequencial automaticamente
            ultimo_centro = CentroCusto.objects.order_by('id').last()
            if ultimo_centro:
                ultimo_codigo = int(ultimo_centro.mascara_centro_custo)
                self.mascara_centro_custo = f'{ultimo_codigo + 1:03d}'
            else:
                self.mascara_centro_custo = '001'
        super(CentroCusto, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.descricao} ({self.mascara_centro_custo})"
class CentroCusto(models.Model):
    id = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=100, blank=False, null=False)
    mascara_centro_custo = models.CharField(max_length=3)
    is_active = models.BooleanField(default=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        db_index=True,
        db_constraint=False
    )

    class Meta:
        unique_together = (('empresa', 'mascara_centro_custo'),)
        verbose_name = 'Centro de Custo'
        verbose_name_plural = 'Centros de Custo'

    def save(self, *args, **kwargs):
        # Gera sequência por tenant
        tenant = get_current_tenant()
        if not self.mascara_centro_custo:
            qs = CentroCusto.objects.filter(empresa=tenant) if tenant else CentroCusto.objects.all()
            ultimo = qs.order_by('id').last()
            if ultimo:
                codigo = int(ultimo.mascara_centro_custo)
                self.mascara_centro_custo = f'{codigo + 1:03d}'
            else:
                self.mascara_centro_custo = '001'
        super().save(*args, **kwargs)
