from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('<int:pk>/sign/', views.document_sign, name='document_sign'),
    path('batch-sign/', views.batch_sign, name='batch_sign'),
    path('api-settings/', views.api_settings, name='api_settings'),
    path('api-settings/token/create/', views.token_create, name='token_create'),
    path('api-settings/token/<int:pk>/revoke/', views.token_revoke, name='token_revoke'),
    path('api-settings/profile/create/', views.profile_create, name='profile_create'),
    path('api-settings/profile/<int:pk>/delete/', views.profile_delete, name='profile_delete'),
]
