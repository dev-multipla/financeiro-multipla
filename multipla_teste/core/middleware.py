# core/middleware.py
from .db_router import _thread_locals

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tid = request.headers.get("X-Company-ID")
        # Se for 'all' ou vazio, limpa (usa default)
        _thread_locals.tenant_id = None if not tid or tid == "all" else tid
        response = self.get_response(request)
        return response
