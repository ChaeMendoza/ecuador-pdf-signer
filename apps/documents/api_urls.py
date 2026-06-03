from django.urls import path
from . import api_views

urlpatterns = [
    path('sign/individual/', api_views.api_sign_individual, name='api_sign_individual'),
    path('sign/batch/', api_views.api_sign_batch, name='api_sign_batch'),
    path('documents/<int:pk>/download/', api_views.api_document_download, name='api_document_download'),
    path('profiles/', api_views.api_profiles_list, name='api_profiles_list'),
]
