from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    STATUS_CHOICES = (
        ('uploaded', 'Subido'),
        ('signed', 'Firmado'),
    )
    
    SOURCE_CHOICES = (
        ('web', 'Web'),
        ('api', 'API'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    original_file = models.FileField(upload_to='documents/original/')
    signed_file = models.FileField(upload_to='documents/signed/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='web')
    created_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Coordenadas de firma
    signature_page = models.IntegerField(null=True, blank=True)
    signature_x = models.FloatField(null=True, blank=True)
    signature_y = models.FloatField(null=True, blank=True)
    signature_width = models.FloatField(null=True, blank=True)
    signature_height = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"Documento {self.id} de {self.user.username} ({self.status}) [{self.source}]"


class SignatureProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signature_profiles')
    name = models.CharField(max_length=100, help_text="Nombre del perfil (ej: Escuela de Derechos)")
    description = models.TextField(blank=True, null=True, help_text="Descripción o notas del perfil")
    page = models.IntegerField(default=1, help_text="Página donde se aplicará la firma (inicia en 1)")
    x = models.FloatField(help_text="Coordenada X en puntos PDF")
    y = models.FloatField(help_text="Coordenada Y en puntos PDF")
    width = models.FloatField(default=200, help_text="Ancho de la firma en puntos")
    height = models.FloatField(default=50, help_text="Alto de la firma en puntos")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil '{self.name}' de {self.user.username} (Pág {self.page}: {self.width}x{self.height})"


class SignatureBatch(models.Model):
    SOURCE_CHOICES = (
        ('web', 'Web'),
        ('api', 'API'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signature_batches')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='web')
    document_count = models.IntegerField(help_text="Cantidad de documentos firmados en este lote")
    signature_profile = models.ForeignKey(SignatureProfile, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lote #{self.id} ({self.document_count} docs) de {self.user.username} [{self.source}]"

