from django.http import JsonResponse
from functools import wraps
from .models import APIToken

def api_token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({
                'error': 'Falta el encabezado de autorización (Authorization)'
            }, status=401)
        
        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() not in ('token', 'bearer'):
                return JsonResponse({
                    'error': 'Formato de token inválido. Use "Token <token_key>" o "Bearer <token_key>"'
                }, status=401)
            
            token_key = parts[1]
            api_token = APIToken.objects.select_related('user').get(token=token_key, is_active=True)
            
            # Autenticar la petición asignando el usuario al request
            request.user = api_token.user
            request.api_token = api_token
            
        except APIToken.DoesNotExist:
            return JsonResponse({
                'error': 'Token de API inválido o inactivo'
            }, status=401)
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view
