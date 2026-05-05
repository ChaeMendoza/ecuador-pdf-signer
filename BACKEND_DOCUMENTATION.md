# 🔧 Documentación Técnica - Backend y API

## 📊 Modelos

### Document Model
```python
class Document(models.Model):
    # ... otros campos ...
    
    # Coordenadas de firma (se guardan después de firmar)
    signature_page = models.IntegerField(null=True, blank=True)
    signature_x = models.FloatField(null=True, blank=True)
    signature_y = models.FloatField(null=True, blank=True)
    signature_width = models.FloatField(null=True, blank=True)
    signature_height = models.FloatField(null=True, blank=True)
```

**Nota**: Estos campos se rellenan con los valores usados durante la firma para auditoría/referencia.

## 📋 Formularios

### DocumentForm
```python
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['original_file']
```
Solo permite subir el PDF original.

### SignDocumentForm
```python
class SignDocumentForm(forms.Form):
    p12_file = forms.FileField(...)
    password = forms.CharField(widget=forms.PasswordInput)
    
    # Coordenadas (desde la interfaz visual o entrada numérica)
    page = forms.IntegerField(widget=forms.HiddenInput(), initial=1)
    x = forms.FloatField(widget=forms.HiddenInput(), initial=50)
    y = forms.FloatField(widget=forms.HiddenInput(), initial=50)
    width = forms.FloatField(widget=forms.HiddenInput(), initial=200)
    height = forms.FloatField(widget=forms.HiddenInput(), initial=50)
```

### BatchSignForm
```python
class BatchSignForm(forms.Form):
    documents = forms.FileField(
        widget=MultipleFileInput(),
        required=False
    )
    p12_file = forms.FileField(...)
    password = forms.CharField(...)
    
    # Coordenadas para todos los documentos
    page = forms.IntegerField(label='Página', initial=1, min_value=1)
    x = forms.FloatField(label='Posición X (puntos)', initial=50, min_value=0)
    y = forms.FloatField(label='Posición Y (puntos)', initial=50, min_value=0)
    width = forms.FloatField(label='Ancho (puntos)', initial=200, min_value=10)
    height = forms.FloatField(label='Alto (puntos)', initial=50, min_value=10)
```

## 🔄 Flujo de Firma Individual

```
1. GET /documents/<id>/sign/
   └─> Renderiza template con formulario vacío
       Valores iniciales: width=200, height=50

2. Canvas renderiza PDF
   └─> Usuario ajusta posición visualmente
       └─> JavaScript actualiza campos ocultos

3. Usuario ajusta tamaño
   └─> JavaScript calcula conversión canvas→PDF
       └─> Actualiza campos width y height

4. POST /documents/<id>/sign/
   ├─> Validar SignDocumentForm
   ├─> Extraer:
   │   - p12_file (certificado)
   │   - password (contraseña)
   │   - page, x, y, width, height (coordenadas)
   │
   ├─> Llamar sign_pdf_service()
   │   ├─> Cargar certificado
   │   ├─> Generar estampa con dimensiones exactas
   │   ├─> Aplicar firma al PDF
   │   └─> Retornar ruta del PDF firmado
   │
   ├─> Guardar archivo firmado
   ├─> Actualizar Document:
   │   - status = 'signed'
   │   - signed_at = now()
   │   - signature_page, signature_x, signature_y, signature_width, signature_height
   │
   └─> Redirect a document_list
```

## 🎁 Flujo de Firma Masiva

```
1. GET /documents/batch-sign/
   └─> Renderiza template con formulario

2. POST /documents/batch-sign/
   ├─> Validar BatchSignForm
   ├─> Validar número de documentos (≤ 100)
   │
   ├─> Extraer parámetros:
   │   - documents[] (lista de archivos)
   │   - page, x, y, width, height (coordenadas)
   │
   ├─> Validar compatibilidad de dimensiones:
   │   FOR each document:
   │   ├─> Guardar temporalmente en /tmp/
   │   ├─> Leer página especificada
   │   ├─> Obtener mediabox (ancho, alto)
   │   ├─> Comparar con referencia
   │   │   IF variacción > 10pt:
   │   │   └─> Retornar error "Dimensiones incompatibles"
   │   └─> Limpiar /tmp/
   │
   ├─> Crear archivo ZIP en memoria (BytesIO)
   │
   ├─> Procesar cada documento:
   │   FOR each document:
   │   ├─> Guardar temporalmente
   │   ├─> Llamar sign_pdf_service()
   │   ├─> Agregar al ZIP con nombre "signed_<original>"
   │   └─> Limpiar /tmp/
   │
   └─> Descargar ZIP como response
```

## 🖨️ Servicio de Firma Digital

### Firma `sign_pdf_service()`

```python
def sign_pdf_service(
    input_pdf_path: str,
    p12_content: bytes,
    password: str,
    page: int = 1,        # 1-indexed (1 = primera página)
    x: float = 50,        # Coordenada X en puntos PDF
    y: float = 50,        # Coordenada Y en puntos PDF (desde abajo)
    width: float = 250,   # Ancho de firma en puntos
    height: float = 60,   # Alto de firma en puntos
) -> str:
    """
    Firma un PDF y retorna la ruta del archivo firmado temporal.
    
    Proceso:
    1. Guardar p12 temporalmente
    2. Extraer nombre del signer del certificado
    3. Cargar certificado con pyHanko SimpleSigner
    4. Generar PNG de estampa (QR + texto)
    5. Crear imagen PIL a partir del PNG
    6. Construir TextStampStyle con la imagen como fondo
    7. Crear SigFieldSpec con las coordenadas exactas
    8. Firmar el PDF usando IncrementalPdfFileWriter
    9. Retornar ruta del PDF firmado
    10. Limpiar archivos temporales
    
    Excepciones:
    - ValueError: Si las credenciales son inválidas
    - PDFError: Si el PDF está dañado o no es soportado
    - Exception: Error general de firma
    """
```

### Funciones Auxiliares

#### `get_pdf_page_size(pdf_path: str, page: int = 1) -> tuple[float, float]`
```python
"""Retorna (ancho, alto) de una página PDF en puntos."""
# Uso: width_pt, height_pt = get_pdf_page_size('document.pdf', page=1)
```

#### `_extract_cn_from_p12(p12_bytes: bytes, password: str) -> str`
```python
"""Extrae Common Name del certificado para mostrar como signer."""
# Retorna: "Juan Pérez" (o "Firmante" si no se puede extraer)
```

## 🎨 Generación de Estampa

Ubicado en `apps/signing/stamp.py`:

```python
def generate_signature_stamp(
    signer_name: str,
    document_path: str,
    timestamp: datetime,
    width_pt: float,
    height_pt: float,
) -> bytes:
    """
    Genera PNG con QR + información de firma.
    
    Layout:
    ┌─────────────────────────────┐
    │ [QR] │ Signer: Juan Pérez  │
    │      │ Doc: documento.pdf  │
    │      │ Time: 2026-05-05... │
    └─────────────────────────────┘
    
    El QR codifica:
    - Nombre del signer
    - Hash del documento
    - Timestamp
    """
```

## 🔌 Vistas

### document_sign(request, pk)

```python
@login_required
def document_sign(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SignDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # Extraer valores desde el formulario
            width = form.cleaned_data['width']  # Ahora configurable
            height = form.cleaned_data['height']  # Ahora configurable
            
            # ... resto de la lógica
```

### batch_sign(request)

```python
@login_required
def batch_sign(request):
    # ... validación de documentos ...
    
    # Nota: Usa los mismos parámetros width/height para todos
    for doc_file in documents:
        signed_pdf_path = sign_pdf_service(
            tmp_pdf_path, p12_content, password,
            page=page, x=x, y=y,
            width=width,  # Mismo para todos
            height=height  # Mismo para todos
        )
```

## ✅ Validaciones

### En el Formulario (Django)
```python
# Automáticamente por Field types
- IntegerField: Solo acepta enteros
- FloatField: Solo acepta números decimales
- min_value: Validación mínima
```

### En la Vista
```python
# Antes de firmar
if len(documents) > 100:
    messages.error(request, 'No se pueden procesar más de 100 documentos a la vez.')
    return redirect('batch_sign')

# Validación de dimensiones PDF
size = get_pdf_page_size(tmp_pdf_path, page)
if abs(size[0] - reference_size[0]) > 10:
    messages.error(request, f'Dimensiones incompatibles...')
    return redirect('batch_sign')
```

### En pyHanko
```python
# Al crear SigFieldSpec:
box_coords = (x, y, x + width, y + height)  # Validación automática

# Al firmar:
# - Verifica que el campo esté dentro de la página
# - Valida que sea un PDF válido
```

## 📈 Mejoras Implementadas

| Característica | Antes | Después |
|---------------|-------|---------|
| Tamaño de firma | Fijo (200x50) | **Configurable (50-400 x 30-200 pt)** |
| Control de tamaño | Manual en código | **Interfaz visual con drag/resize** |
| Inputs numéricos | Solo posición | **Posición + Tamaño** |
| Aspect ratio | No aplicable | **Toggle para mantener proporción** |
| Validación | Backend solo | **Frontend + Backend** |
| Batch signing | Mismo tamaño siempre | **Reutilización de configuración** |

## 🐛 Debugging

### Logs Útiles

```python
# En views.py, después de sign_pdf_service():
print(f"Firma aplicada: {page=}, {x=}, {y=}, {width=}, {height=}")
print(f"Documento guardado: {document.signed_file.path}")

# En services.py:
print(f"Estampa generada: {width_pt}x{height_pt}")
print(f"PDF firmado en: {output_pdf_path}")
```

### Errores Comunes

**"ValueError: ClearableFileInput doesn't support..."**
- Solución: Usar `MultipleFileInput` en lugar de `ClearableFileInput`

**"Box coordinates out of bounds"**
- Solución: Validar que `x + width <= page_width` y `y + height <= page_height`

**"Dimensiones incompatibles en batch"**
- Solución: Reducir tolerancia de 10 a 5 pts, o usar documentos del mismo formato

## 🔐 Seguridad

### Manejo del Certificado
```python
# El certificado se carga en memoria
with tempfile.NamedTemporaryFile(delete=False, suffix='.p12') as p12_tmp:
    p12_tmp.write(p12_content)  # Solo escritura temporal
    p12_temp_path = p12_tmp.name

# Se usa solo para extraer datos
signer = signers.SimpleSigner.load_pkcs12(
    p12_temp_path, passphrase=password.encode('utf-8')
)

# Se destruye inmediatamente
finally:
    if os.path.exists(p12_temp_path):
        os.remove(p12_temp_path)  # Limpieza segura
```

### La Contraseña
- Nunca se almacena en la DB
- Solo se mantiene en memoria durante la firma
- Se destruye después de procesar

## 📦 Dependencias Modificadas

```
pyHanko[image-support]>=0.21.0  # Ya soporta width/height
Django>=5.0  # Soporte para FileInput mejorado
Pillow>=10.0.0  # Para generación de imágenes
```

## 🚀 Implementación de Nuevas Características

Para agregar futuras mejoras:

### Agregar nueva validación
```python
# En forms.py o views.py
if width > 400 or width < 50:
    raise ValidationError("Ancho fuera de rango permitido")
```

### Agregar nueva dimensión (ej: rotación)
```python
# 1. Agregar campo en modelo
rotation = models.IntegerField(choices=[(0, '0°'), (90, '90°')], default=0)

# 2. Agregar input en formulario
rotation = forms.ChoiceField(choices=[(0, '0°'), (90, '90°')])

# 3. Pasar a sign_pdf_service
signed_pdf_path = sign_pdf_service(..., rotation=rotation)

# 4. Implementar en stamp.py
def generate_signature_stamp(..., rotation=0):
    # Generar imagen y rotarla
```

## 📊 Estadísticas de Uso

Para monitoreo, se pueden agregar logs:

```python
import logging
logger = logging.getLogger(__name__)

# En cada firma
logger.info(f"Firma realizada: user={user}, width={width}, height={height}")
```

---

**Última actualización**: 5 de mayo de 2026  
**Versión**: 2.0  
**Autor**: Sistema de Firma Digital
