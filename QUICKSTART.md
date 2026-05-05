# 🚀 Quick Start - Redimensionamiento de Firmas

## 5 Minutos para Empezar

### ✅ Pre-requisitos
- Django 5.0+
- Python 3.11+
- PyHanko instalado

### 📦 Cambios Necesarios

Ya están implementados en los archivos:
- ✅ `apps/documents/forms.py` - Formularios actualizados
- ✅ `templates/documents/document_sign.html` - UI interactiva con JS
- ✅ `templates/documents/batch_sign.html` - Interfaz mejorada

### 🎯 Uso Rápido

#### Opción 1: Firma Individual
```bash
1. Navega a http://localhost:8000/documents/
2. Selecciona un documento
3. Haz clic en el PDF para colocar la firma
4. Arrastra las esquinas para redimensionar (nuevo)
5. O escribe valores en los inputs numéricos (nuevo)
6. Carga tu certificado y contraseña
7. Presiona "Firmar Documento"
```

#### Opción 2: Firma Masiva
```bash
1. Navega a http://localhost:8000/documents/batch-sign/
2. Selecciona múltiples PDFs
3. Define posición: X, Y, Página
4. Define tamaño: Ancho (pt), Alto (pt)  [NUEVO]
5. Carga certificado y contraseña
6. Presiona "Firmar Documentos y Descargar ZIP"
```

### 🔧 Integración con Django

#### Si heredas de Document model
```python
# El modelo ya tiene los campos:
signature_width = models.FloatField(null=True, blank=True)
signature_height = models.FloatField(null=True, blank=True)

# Se completan automáticamente después de firmar
document.signature_width = 200.0
document.signature_height = 50.0
document.save()
```

#### Si heredas de SignDocumentForm
```python
# Los campos ya existen:
# - width (default 200)
# - height (default 50)

# Se pueden sobrescribir:
class MySignForm(SignDocumentForm):
    width = forms.FloatField(
        initial=250,  # Tu tamaño por defecto
        min_value=50,
        max_value=400
    )
```

#### Si necesitas personalizar en views.py
```python
def document_sign(request, pk):
    if request.method == 'POST':
        form = SignDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # Los datos ya incluyen width/height
            width = form.cleaned_data['width']
            height = form.cleaned_data['height']
            
            # Pasar a sign_pdf_service
            signed_path = sign_pdf_service(
                input_path, p12_content, password,
                page=page, x=x, y=y,
                width=width,   # Nuevo: configurable
                height=height  # Nuevo: configurable
            )
```

### 📐 Matemática de Coordenadas

Si necesitas convertir manualmente:

```python
# De Canvas (px) a PDF (pt)
scale = 1.4  # Factor de escala visual
pdf_x = canvas_x / scale
pdf_y = (canvas_height / scale) - canvas_y - height_pt

# De PDF (pt) a Canvas (px)
canvas_x = pdf_x * scale
canvas_y = (canvas_height / scale) - pdf_y - height_pt
```

### 🎨 Personalizar Tamaño Por Defecto

#### En el template
```html
<!-- document_sign.html línea ~30 -->
<script>
    let SIGNATURE_WIDTH_PT = 200;   // Cambiar aquí
    let SIGNATURE_HEIGHT_PT = 50;   // Cambiar aquí
</script>
```

#### En el formulario
```python
# forms.py
class SignDocumentForm(forms.Form):
    width = forms.FloatField(
        initial=250,  # Tu valor por defecto
        ...
    )
    height = forms.FloatField(
        initial=60,   # Tu valor por defecto
        ...
    )
```

### 🔍 Debugging

#### Console del Navegador (F12)
```javascript
// Ver coordenadas actuales
console.log(`Width: ${SIGNATURE_WIDTH_PT}, Height: ${SIGNATURE_HEIGHT_PT}`);

// Ver tamaño en canvas
console.log(`Canvas: ${signatureBox.offsetWidth}x${signatureBox.offsetHeight}`);

// Ver factor de escala
console.log(`Scale: ${scale}`);
```

#### Logs de Django
```python
# En views.py, después de firmar
print(f"Firma aplicada: {width=}, {height=}")
print(f"Documento guardado: {document.signed_file.path}")
```

### 🧪 Pruebas Rápidas

```bash
# Prueba unitaria básica
python manage.py test apps.documents.tests.SignDocumentFormTest

# Crear datos de prueba
python manage.py shell
>>> from apps.documents.models import Document
>>> from django.contrib.auth.models import User
>>> u = User.objects.create_user('test', 'test@test.com', 'pass')
>>> d = Document.objects.create(user=u, original_file='docs/test.pdf')
>>> d.save()

# Verificar coordenadas guardadas
>>> print(d.signature_width, d.signature_height)
```

### 🚨 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Resize no funciona | Recargar página (Ctrl+F5) |
| Inputs no actualizan | Verificar que JavaScript está habilitado |
| Firma se sale del PDF | Reducir tamaño o mover posición |
| Error "incompatibles" en batch | Asegurar que todos los PDFs sean A4 |
| Width/height = null en BD | Verificar que form.is_valid() es true |

### 📞 Documentación Completa

Para info más detallada, ver:
- [USER_GUIDE_ES.md](USER_GUIDE_ES.md) - Guía de usuario
- [SIGNATURE_SIZING_GUIDE.md](SIGNATURE_SIZING_GUIDE.md) - Detalles técnicos
- [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) - API y validaciones
- [TEST_PLAN.md](TEST_PLAN.md) - Casos de prueba

### ✨ Características Principales

```
┌─────────────────────────────────────────┐
│ NUEVA FUNCIONALIDAD v2.0               │
├─────────────────────────────────────────┤
│ ✓ Drag en esquinas (resize)            │
│ ✓ Inputs numéricos (ancho/alto)        │
│ ✓ Aspect ratio lock                    │
│ ✓ Validación en tiempo real            │
│ ✓ Batch signing compatible             │
│ ✓ Previsualización exacta              │
└─────────────────────────────────────────┘
```

---

**¿Necesitas más ayuda?**

1. Revisa los ejemplos en [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md)
2. Consulta los test cases en [TEST_PLAN.md](TEST_PLAN.md)
3. Verifica el JavaScript en `templates/documents/document_sign.html`

**Última actualización:** 5 de mayo de 2026
