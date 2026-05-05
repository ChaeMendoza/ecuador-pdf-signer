from django import forms
from .models import Document

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

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

class BatchSignForm(forms.Form):
    documents = forms.FileField(
        widget=MultipleFileInput(),
        label='Documentos PDF',
        help_text='Selecciona múltiples archivos PDF para firmar.',
        required=False
    )
    p12_file = forms.FileField(label='Certificado (.p12 o .pfx)', help_text='Sube tu archivo de firma electrónica.')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña del certificado')
    
    # Coordenadas de firma
    page = forms.IntegerField(label='Página', initial=1, min_value=1)
    x = forms.FloatField(label='Posición X (puntos)', initial=50, min_value=0)
    y = forms.FloatField(label='Posición Y (puntos)', initial=50, min_value=0)
    width = forms.FloatField(label='Ancho (puntos)', initial=200, min_value=10)
    height = forms.FloatField(label='Alto (puntos)', initial=50, min_value=10)
