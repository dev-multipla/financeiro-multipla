from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from contas_pagar.models import ContaAPagar
from django.utils import timezone

class UltimasContasPagasViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Cria algumas contas a pagar para o teste
        for i in range(5):
            ContaAPagar.objects.create(
                descricao=f"Conta {i+1}",
                valor=100.0 + i,
                data_pagamento=timezone.now(),
                status='pago'
            )
        
        # Endpoint URL
        self.url = reverse('ultimas-contas-pagas')

    def test_ultimas_contas_pagas(self):
        response = self.client.get(self.url)
        
        # Verifica se a resposta foi 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica se retornou exatamente 3 contas pagas
        self.assertEqual(len(response.data), 3)
        
        # Verifica se os dados retornados correspondem às últimas contas pagas
        ultima_conta = ContaAPagar.objects.order_by('-data_pagamento')[0]
        self.assertEqual(response.data[0]['descricao'], ultima_conta.descricao)
        self.assertEqual(response.data[0]['valor'], ultima_conta.valor)
        self.assertEqual(response.data[0]['status'], ultima_conta.status)
