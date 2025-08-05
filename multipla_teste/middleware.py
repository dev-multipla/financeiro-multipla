# middleware.py
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

class TokenValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.COOKIES.get('access_token')
        if token:
            try:
                AccessToken(token)
            except (TokenError, InvalidToken):
                return Response({'message': 'Token expired, please login again'}, status=status.HTTP_401_UNAUTHORIZED)
        response = self.get_response(request)
        return response
