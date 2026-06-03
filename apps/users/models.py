import secrets
from django.db import models
from django.contrib.auth.models import User

class APIToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=100, help_text="Nombre descriptivo para identificar quién usa este token")
    token = models.CharField(max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # Genera un token seguro de 64 caracteres hexadecimales
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Token '{self.name}' para {self.user.username} ({'Activo' if self.is_active else 'Inactivo'})"
