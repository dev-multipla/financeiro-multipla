# multipla_teste/tenant_router.py

from threading import local
from django.conf import settings
from django.db import connections

_thread_locals = local()

def set_current_tenant(tenant):
    """
    Define o tenant atual na variável thread-local.
    """
    _thread_locals.tenant = tenant

def get_current_tenant():
    """
    Retorna o tenant atual armazenado em thread-local (ou None se não existir).
    """
    return getattr(_thread_locals, 'tenant', None)

class TenantRouter:
    """
    Roteia ORM para 'tenant_X' apenas para apps scoped. 
    Global apps (auth, contenttypes, sessions, admin, empresas, usuarios)
    continuam no default.
    """
    SHARED_APPS = {
        'auth',
        'contenttypes',
        'sessions',
        'admin',
        'admin_honeypot',  # se usar outros
        'empresas',
        'usuarios',
    }

    def db_for_read(self, model, **hints):
        # 1) Se for um app “compartilhado”, vai para default
        if model._meta.app_label in self.SHARED_APPS:
            return 'default'
        # 2) Se houver tenant ativo e o alias existir, usa tenant_{id}
        tenant = get_current_tenant()
        if tenant:
            alias = f"tenant_{tenant.id}"
            if alias in settings.DATABASES:
                return alias
        # 3) Caso contrário, default
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.SHARED_APPS:
            return 'default'
        tenant = get_current_tenant()
        if tenant:
            alias = f"tenant_{tenant.id}"
            if alias in settings.DATABASES:
                return alias
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        db_obj1 = getattr(obj1._state, 'db', None)
        db_obj2 = getattr(obj2._state, 'db', None)
        if db_obj1 and db_obj2:
            return db_obj1 == db_obj2
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Migrar shared apps só em default
        if app_label in self.SHARED_APPS:
            return db == 'default'
        # Migrar todos os outros apps em qualquer tenant_*
        if db == 'default':
            return True
        return db.startswith('tenant_')
