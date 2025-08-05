# decorators.py
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(self, *args, **kwargs):
        request = args[0]
        token = request.COOKIES.get('access_token')
        if token:
            try:
                AccessToken(token)
            except (TokenError, InvalidToken):
                return Response({'message': 'Token expired, please login again'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'message': 'Token not found'}, status=status.HTTP_401_UNAUTHORIZED)
        return view_func(self, *args, **kwargs)
    return _wrapped_view
