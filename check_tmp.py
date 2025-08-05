import os
import django

# Configure o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multipla_teste.settings')
django.setup()

from contratos.models import Contrato
from contas_pagar.models import FormaPagamento, Projeto

# Verifique se os registros existem no banco de dados
contrato_existe = Contrato.objects.filter(id=1).exists()
forma_pagamento_existe = FormaPagamento.objects.filter(id=1).exists()
projeto_existe = Projeto.objects.filter(id=1).exists()

print(f"Contrato existe: {contrato_existe}")  # Deve retornar True
print(f"Forma de Pagamento existe: {forma_pagamento_existe}")  # Deve retornar True
print(f"Projeto existe: {projeto_existe}")  # Deve retornar True
