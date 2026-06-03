from django.contrib import admin
from .models import APIToken

@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username', 'token')
    raw_id_fields = ('user',)
