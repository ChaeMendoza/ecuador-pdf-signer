from django.contrib import admin
from .models import Document, SignatureProfile, SignatureBatch

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'source', 'created_at', 'signed_at')
    list_filter = ('status', 'source', 'created_at', 'signed_at')
    search_fields = ('original_file', 'signed_file', 'user__username')
    raw_id_fields = ('user',)

@admin.register(SignatureProfile)
class SignatureProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'page', 'x', 'y', 'width', 'height', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username', 'description')
    raw_id_fields = ('user',)

@admin.register(SignatureBatch)
class SignatureBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'source', 'document_count', 'signature_profile', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('user__username', 'signature_profile__name')
    raw_id_fields = ('user', 'signature_profile')
