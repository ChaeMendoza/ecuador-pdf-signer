from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    STATUS_CHOICES = (
        ('uploaded', 'Subido'),
        ('signed', 'Firmado'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    original_file = models.FileField(upload_to='documents/original/')
    signed_file = models.FileField(upload_to='documents/signed/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Coordenadas de firma
    signature_page = models.IntegerField(null=True, blank=True)
    signature_x = models.FloatField(null=True, blank=True)
    signature_y = models.FloatField(null=True, blank=True)
    signature_width = models.FloatField(null=True, blank=True)
    signature_height = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"Documento {self.id} de {self.user.username} ({self.status})"
