from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['original_file']
        labels = {
            'original_file': 'Archivo PDF Original'
        }

class SignDocumentForm(forms.Form):
    p12_file = forms.FileField(label='Certificado (.p12 o .pfx)', help_text='Sube tu archivo de firma electrónica.')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña del certificado')
    
    # Campos ocultos para las coordenadas
    page = forms.IntegerField(widget=forms.HiddenInput(), initial=1)
    x = forms.FloatField(widget=forms.HiddenInput(), initial=50)
    y = forms.FloatField(widget=forms.HiddenInput(), initial=50)
    width = forms.FloatField(widget=forms.HiddenInput(), initial=200)
    height = forms.FloatField(widget=forms.HiddenInput(), initial=50)
