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
    
    # Sellado de Tiempo (TSA)
    tsa_url = forms.ChoiceField(
        choices=[
            ('', 'Sin sellado de tiempo (usar reloj local)'),
            ('http://timestamp.digicert.com', 'DigiCert (Gratuito - Pruebas)'),
            ('https://tsa.uanataca.com/tsa/tss03', 'Uanataca Producción (/tsa/tss03)'),
            ('https://tsa.uanataca.com/tsa/tss02', 'Uanataca Producción (/tsa/tss02)'),
            ('https://tsa.sandbox.uanataca.com/tsa/tss03', 'Uanataca Sandbox/Pruebas'),
            ('https://tsa.uanatacaec.com/tsa', 'Uanataca (Ecuador) - /tsa'),
            ('https://tsa.uanatacaec.com/tsa/tss03', 'Uanataca (Ecuador) - /tsa/tss03'),
            ('http://tsa.funcionjudicial.gob.ec', 'Consejo de la Judicatura'),
            ('http://tsa.securitydata.net.ec', 'Security Data'),
            ('http://tsa.bce.ec', 'Banco Central del Ecuador'),
            ('custom', 'Otro (URL personalizada)...')
        ],
        required=False,
        label='Autoridad de Sellado de Tiempo (TSA)',
        initial='',
        help_text='Permite certificar la fecha y hora oficial de la firma.'
    )
    custom_tsa_url = forms.URLField(
        required=False,
        label='URL de TSA Personalizada',
        widget=forms.URLInput(attrs={'placeholder': 'https://ejemplo.com/tsa'}),
        help_text='Especifica la URL del servidor TSA si seleccionaste "Otro".'
    )
    tsa_username = forms.CharField(
        required=False,
        label='Usuario de TSA',
        widget=forms.TextInput(attrs={'placeholder': 'Opcional (para TSAs comerciales)'}),
        help_text='Ingresa el usuario si tu TSA requiere autenticación.'
    )
    tsa_password = forms.CharField(
        required=False,
        label='Contraseña de TSA',
        widget=forms.PasswordInput(attrs={'placeholder': 'Opcional'}),
        help_text='Ingresa la contraseña si tu TSA requiere autenticación.'
    )
    
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
    
    # Sellado de Tiempo (TSA)
    tsa_url = forms.ChoiceField(
        choices=[
            ('', 'Sin sellado de tiempo (usar reloj local)'),
            ('http://timestamp.digicert.com', 'DigiCert (Gratuito - Pruebas)'),
            ('https://tsa.uanataca.com/tsa/tss03', 'Uanataca Producción (/tsa/tss03)'),
            ('https://tsa.uanataca.com/tsa/tss02', 'Uanataca Producción (/tsa/tss02)'),
            ('https://tsa.sandbox.uanataca.com/tsa/tss03', 'Uanataca Sandbox/Pruebas'),
            ('https://tsa.uanatacaec.com/tsa', 'Uanataca (Ecuador) - /tsa'),
            ('https://tsa.uanatacaec.com/tsa/tss03', 'Uanataca (Ecuador) - /tsa/tss03'),
            ('http://tsa.funcionjudicial.gob.ec', 'Consejo de la Judicatura'),
            ('http://tsa.securitydata.net.ec', 'Security Data'),
            ('http://tsa.bce.ec', 'Banco Central del Ecuador'),
            ('custom', 'Otro (URL personalizada)...')
        ],
        required=False,
        label='Autoridad de Sellado de Tiempo (TSA)',
        initial='',
        help_text='Permite certificar la fecha y hora oficial de la firma.'
    )
    custom_tsa_url = forms.URLField(
        required=False,
        label='URL de TSA Personalizada',
        widget=forms.URLInput(attrs={'placeholder': 'https://ejemplo.com/tsa'}),
        help_text='Especifica la URL del servidor TSA si seleccionaste "Otro".'
    )
    tsa_username = forms.CharField(
        required=False,
        label='Usuario de TSA',
        widget=forms.TextInput(attrs={'placeholder': 'Opcional (para TSAs comerciales)'}),
        help_text='Ingresa el usuario si tu TSA requiere autenticación.'
    )
    tsa_password = forms.CharField(
        required=False,
        label='Contraseña de TSA',
        widget=forms.PasswordInput(attrs={'placeholder': 'Opcional'}),
        help_text='Ingresa la contraseña si tu TSA requiere autenticación.'
    )
    
    # Coordenadas de firma
    page = forms.IntegerField(label='Página', initial=1, min_value=1)
    x = forms.FloatField(label='Posición X (puntos)', initial=50, min_value=0)
    y = forms.FloatField(label='Posición Y (puntos)', initial=50, min_value=0)
    width = forms.FloatField(label='Ancho (puntos)', initial=200, min_value=10)
    height = forms.FloatField(label='Alto (puntos)', initial=50, min_value=10)
