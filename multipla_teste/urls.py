from django.contrib import admin
from django.urls import path, include
#multipla_teste/url.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from fornecedores.views import FornecedorViewSet, FornecedorSelectViewSet, FornecedorListViewSet
from clientes.views import ClienteViewSet, ClienteSelectViewSet, ClientListViewSet
from contratos.views import ContratoViewSet, ContratoSelectViewSet, ContratoListViewSet
from projetos.views import ProjetoViewSet, ProjetoSelectViewSet, ProjetoListViewSet
from pagamentos.views import FormaPagamentoViewSet, FormaPagamentoSelectViewSet, FormaPagamentoViewSet
from contas_pagar import views
from contas_pagar.views import ContaAPagarViewSet, ContaAReceberViewSet, RelatorioProjecoesViewSet, ConsolidatedViewSet
from .views import UserCreate, LogoutView
from contas_pagar.views import ContaAPagarViewSet, ContaAReceberViewSet, RelatorioOperacionalViewSet, ConsolidatedViewSet
from .views import UserCreate, LogoutView
from usuarios.views import (
    UserViewSet,
    UserCreateView,
    MeView,
    LogoutView,
    MinhasEmpresasViewSet,
    login_view,
)
from usuarios.serializers import CustomTokenObtainPairSerializer
from empresas.views import EmpresaViewSet, FilialViewSet, EmpresaListViewSet, FilialListViewSet
from contratos import views as contratos_views
from financeiro.views import ContaFinanceiraViewSet, CentroCustoViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = routers.DefaultRouter()
router.register(r'fornecedores', FornecedorViewSet)
router.register(r'clientes', ClienteViewSet)
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from notifications.views import NotificationViewSet

from funcionarios.views import FuncionarioViewSet, FuncionarioSelectViewSet, FuncionarioListViewSet
#from relatorios.views import RelatorioResultadoPorContratoView
from relatorios.views import RelatorioResultadoPorContratoViewSet,  RelatorioResultadoPorProjetoViewSet

router = routers.DefaultRouter()
router.register(r'minhas-empresas', MinhasEmpresasViewSet, basename='minhas-empresas')
router.register(r'usuarios', UserViewSet)
router.register(r'fornecedores', FornecedorViewSet)
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'contratos', ContratoViewSet)
router.register(r'projetos', ProjetoViewSet)
router.register(r'formas-pagamento', FormaPagamentoViewSet)
router.register(r'select/clientes', ClienteSelectViewSet, basename='cliente-select')
router.register(r'select/fornecedores', FornecedorSelectViewSet, basename='fornecedor-select')
router.register(r'select/contratos', ContratoSelectViewSet, basename='contrato-select')
router.register(r'select/formas-pagamento', FormaPagamentoSelectViewSet, basename='forma-pagamento-select')
router.register(r'select/projetos', ProjetoSelectViewSet, basename='projeto-select')
router.register(r'contas-pagar', views.ContaAPagarViewSet, basename='contapagar')  
router.register(r'contas-receber', views.ContaAReceberViewSet, basename='contareceber')
router.register(r'contas-a-pagar-avulso', views.ContaPagarAvulsoViewSet)
router.register(r'contas-a-receber-avulso', views.ContaReceberAvulsoViewSet)
router.register(
    r'contas-a-pagar-avulso',
    views.ContaPagarAvulsoViewSet,
    basename='contas-a-pagar-avulso'   # ← especifica manualmente
)

router.register(
    r'contas-a-receber-avulso',
    views.ContaReceberAvulsoViewSet,
    basename='contas-a-receber-avulso'   # ← especifica manualmente
)
router.register(r'relatorio-financeiro', views.RelatorioFinanceiroViewSet, basename='relatorio-financeiro')
router.register(r'contas-financeiras', ContaFinanceiraViewSet, basename='contas-financeiras')
router.register(r'centros-custos', CentroCustoViewSet, basename='centrocusto')
router.register(r'empresas', EmpresaViewSet)
router.register(r'filiais', FilialViewSet)
router.register(r'empresas-list', EmpresaListViewSet, basename='empresa-list')
router.register(r'filiais-list', FilialListViewSet, basename='filial-list')
router.register(r'contratos-list', ContratoListViewSet, basename='contrato-list')
router.register(r'projeto-list', ProjetoListViewSet, basename='projeto-list')
router.register(r'cliente-list', ClientListViewSet, basename='cliente-list')
router.register(r'fornecedor-list', FornecedorListViewSet, basename='fornecedor-list')
router.register(r'formas-pagamento', FormaPagamentoViewSet, basename='formas-pagamento')
router.register(r'contas/contapagar/ultima-conta/', ContaAPagarViewSet, basename='contas/contapagar/ultima-conta/' )
router.register(r'contas-receber/ultima-conta', views.ContaAReceberViewSet, basename='contas-receber-ultima-conta')
router.register(r'contas-consolidadas', ConsolidatedViewSet, basename='contas-consolidadas')


router.register(r'funcionarios', FuncionarioViewSet)
router.register(r'funcionarios-select', FuncionarioSelectViewSet, basename='funcionarios-select')
router.register(r'funcionarios-list', FuncionarioListViewSet, basename='funcionarios-list')
router.register(r'relatorio-resultado', RelatorioResultadoPorContratoViewSet, basename='relatorio-resultado')
router.register(r'relatorio-resultado-projeto', RelatorioResultadoPorProjetoViewSet, basename='relatorio-resultado-projeto')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'relatorios/operacional', RelatorioOperacionalViewSet, basename='relatorio-operacional')


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', UserCreate.as_view(), name='user-create'),  # Sem necessidade de decorador
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('login/', login_view, name='login'), 
    path('api/contas-a-pagar/total/', views.TotalContasAPagarView.as_view(), name='total-contas-a-pagar'),
    path('api/contas-a-pagar/proximos-vencimentos/', views.ProximosVencimentosView.as_view(), name='proximos-vencimentos'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', UserCreateView.as_view(), name='user-create'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('login/', login_view, name='login'), 
    path('api/contas-a-pagar/total/', views.TotalContasAPagarView.as_view(), name='total-contas-a-pagar'),
    path(
            'api/contas-a-pagar/proximos_vencimentos/',
            views.ProximosVencimentosViewSet.as_view({'get': 'list'}),
            name='proximos_vencimentos'
        ),

    path('api/contas-a-pagar/contas_pendentes/', views.ContaAPagarViewSet.as_view({'get': 'contas_pendentes'}), name='contas-a-pagar-pendentes'),
    path('api/contas-a-receber/contas_pendentes/', views.ContaAReceberViewSet.as_view({'get': 'contas_pendentes'}), name='contas-a-receber-pendentes'),
    path('api/contratos/preview/', ContratoViewSet.as_view({'post': 'preview'}), name='contratos-preview'),
    
    path('api/contratos/fornecedor/', contratos_views.ContratosFornecedorView.as_view(), name='contratos-fornecedor'),
    path('api/contratos/cliente/', contratos_views.ContratosClienteView.as_view(), name='contratos-cliente'),
    path('api/contratos/<int:pk>/soft_delete/', ContratoViewSet.as_view({'delete': 'soft_delete'}), name='contrato-soft-delete'),
    path('api/contratos/projecoes/', ContratoViewSet.as_view({'post': 'gerar_projecoes'}), name='gerar-projecoes'),
    #path('api/contratos/salvar/', ContratoViewSet.as_view({'post': 'salvar_contrato'}), name='salvar-contrato'),
    path('api/contas-a-pagar/total-pagas-ano/', views.ContaAPagarViewSet.as_view({'get': 'total_pagas_ano'}), name='total-pagas-ano'),
    path('api/contas-a-receber/total-recebidas-ano/', views.ContaAReceberViewSet.as_view({'get': 'total_recebidas_ano'}), name='total-recebidas-ano'),
    path('api/contas-a-pagar/total_faturamento_pagar/', views.ContaAPagarViewSet.as_view({'get': 'total_faturamento_pagar'}), name='total_faturamento_pagar'),
    path('api/contas-a-receber/total_faturamento_receber/', views.ContaAReceberViewSet.as_view({'get': 'total_faturamento_receber'}), name='total_faturamento_receber'),
    path('api/relatorio-projecoes/', RelatorioProjecoesViewSet.as_view({'get': 'gerar_relatorio'}), name='relatorio-projecoes'),
    #path('api/relatorios/resultado-por-contrato/', RelatorioResultadoPorContratoView.as_view(), name='relatorio-resultado-por-contrato'),    
    path('api/contratos/fornecedor/', contratos_views.ContratosFornecedorView.as_view(), name='contratos-fornecedor'),
    path('api/contratos/cliente/', contratos_views.ContratosClienteView.as_view(), name='contratos-cliente'),
    path('api/contratos/<int:pk>/soft_delete/', ContratoViewSet.as_view({'delete': 'soft_delete'}), name='contrato-soft-delete'),
    #path('api/contratos/projecoes/', ContratoViewSet.as_view({'post': 'gerar_projecoes'}), name='gerar-projecoes'),
    #path('api/contratos/salvar/', ContratoViewSet.as_view({'post': 'salvar_contrato'}), name='salvar-contrato'),
    path('api/contas-a-pagar/total-pagas-mes-vencimento/', views.ContaAPagarViewSet.as_view({'get': 'total_pagas_mes_vencimento'}), name='total-pagas-mes-vencimento'),
    path('api/contas-a-pagar/proximo-vencimento-nao-pago/', views.ContaAPagarViewSet.as_view({'get': 'total_pagas_mes_vencimento'}), name='proximo-vencimento-nao-pago'),
    path('api/contas-a-receber/total-recebidas-mes-vencimento/', views.ContaAReceberViewSet.as_view({'get': 'total_recebidas_mes_vencimento'}), name='total-recebidas-mes-vencimento'),
    path('api/contas-a-pagar/total_faturamento_pagar/', views.ContaAPagarViewSet.as_view({'get': 'total_faturamento_pagar'}), name='total_faturamento_pagar'),
    path('api/contas-a-receber/total_faturamento_receber/', views.ContaAReceberViewSet.as_view({'get': 'total_faturamento_receber'}), name='total_faturamento_receber'),
    path('api/relatorio-projecoes/', RelatorioOperacionalViewSet.as_view({'get': 'gerar_relatorio'}), name='relatorio-projecoes'),
    path('api/contas-pagar/<int:pk>/atualizar-status/', 
         ContaAPagarViewSet.as_view({'patch': 'atualizar_status'}), 
         name='conta-pagar-atualizar-status'),
    
    path('api/contas-receber/<int:pk>/atualizar-status/', 
         ContaAReceberViewSet.as_view({'patch': 'atualizar_status'}), 
         name='conta-receber-atualizar-status'),
    


    path('api/contas-a-pagar/proximos_vencimentos/',
        views.ProximosVencimentosViewSet.as_view({'get': 'list'}),
        name='proximos_vencimentos'),
    
    path('api/me/', MeView.as_view(), name='me'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

