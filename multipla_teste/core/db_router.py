# core/db_router.py
from threading import local
from django.conf import settings

_thread_locals = local()

def get_current_tenant():
    return getattr(_thread_locals, "tenant_id", None)

class TenantRouter:
    """Encaminha operações para o banco tenant_{id} baseado no contexto da request."""

    def db_for_read(self, model, **hints):
        tid = get_current_tenant()
        return f"tenant_{tid}" if tid else "default"

    def db_for_write(self, model, **hints):
        tid = get_current_tenant()
        return f"tenant_{tid}" if tid else "default"

    def allow_relation(self, obj1, obj2, **hints):
        # Permite relações se estiverem no mesmo DB
        db1 = obj1._state.db
        db2 = obj2._state.db
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Migrations no default sempre, e em cada tenant só apps *que você queira*
        if db == "default":
            return True
        # se quiser migrar todos apps em tenant, retorne True aqui
        return True
