class NoCacheAuthenticatedMiddleware:
    """
    Middleware para agregar cabeceras anti-cache a todas las respuestas
    donde el usuario esté autenticado. Esto previene que el navegador
    almacene contenido sensible en su caché local y evite la vulnerabilidad
    del botón 'Atrás' después de cerrar sesión.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si el usuario está autenticado, no queremos que el navegador cachee NADA.
        if hasattr(request, 'user') and request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response
