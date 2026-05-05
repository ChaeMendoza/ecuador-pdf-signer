# Guía de Redimensionamiento de Firmas

## 📋 Descripción General

La nueva funcionalidad permite redimensionar las firmas digitales antes de aplicarlas en los documentos PDF. El sistema mantiene:

- **Previsualización en tiempo real** en el canvas del navegador
- **Precisión en coordenadas PDF** (puntos reales, no pixeles del canvas)
- **Validación de límites** para evitar firmas fuera de los bordes del documento
- **Compatibilidad con batch signing** reutilizando la misma configuración

## 🎨 Frontend - Interacción con el Usuario

### Ubicación de controles
- **Documento individual** (`document_sign.html`): Panel derecho con controles de posición y tamaño
- **Firma masiva** (`batch_sign.html`): Formulario único con campos de posición y tamaño

### Métodos de redimensionamiento

#### 1. Drag en esquinas (Visual)
```
┌─────────────────┐
├─ NW  │    │  NE ┤
│      │ Firma │  │
├─ SW  │    │  SE ┤
└─────────────────┘
```
- **NW** (Noroeste): Arrastra la esquina superior izquierda
- **NE** (Noreste): Arrastra la esquina superior derecha
- **SW** (Suroeste): Arrastra la esquina inferior izquierda
- **SE** (Sureste): Arrastra la esquina inferior derecha

Los handles aparecen solo cuando pasas el mouse sobre la firma (`:hover`).

#### 2. Inputs numéricos
```
Ancho:  [200] pt
Alto:   [50]  pt
✓ Mantener proporción
```

- Rango de **ancho**: 50-400 pt
- Rango de **alto**: 30-200 pt
- **Aspect ratio lock**: Cuando está activado, al cambiar un valor, el otro se ajusta automáticamente

### Cálculo de Conversión (Canvas ↔ PDF)

El sistema utiliza una **escala visual** de `1.4x` para mostrar el PDF en el navegador, pero internamente guarda las coordenadas en **puntos PDF** (pt):

```javascript
const scale = 1.4; // Factor de escala visual

// De canvas (píxeles) a PDF (puntos)
pdf_x = canvas_x / scale;
pdf_y = (canvas_height / scale) - canvas_y - height_pt;

// De PDF (puntos) a canvas (píxeles)
canvas_x = pdf_x * scale;
canvas_y = (canvas_height / scale) - pdf_y - height_pt;
```

**Nota sobre Y**: El eje Y es inverso porque:
- En canvas: Y=0 está en la parte superior
- En PDF: Y=0 está en la parte inferior

## 🛠️ Backend - Procesamiento

### Modelo de Datos
```python
class Document(models.Model):
    signature_page = models.IntegerField()     # Número de página (1-indexed)
    signature_x = models.FloatField()          # X en puntos PDF
    signature_y = models.FloatField()          # Y en puntos PDF
    signature_width = models.FloatField()      # Ancho en puntos PDF
    signature_height = models.FloatField()     # Alto en puntos PDF
```

### Servicio de Firma

El servicio `sign_pdf_service()` recibe las dimensiones en puntos PDF:

```python
signed_pdf_path = sign_pdf_service(
    input_pdf_path,
    p12_content,
    password,
    page=1,
    x=50.0,      # Puntos PDF
    y=50.0,      # Puntos PDF
    width=200.0, # Puntos PDF
    height=50.0  # Puntos PDF
)
```

### Generación de Estampa

La imagen de firma se genera con las dimensiones solicitadas:

```python
stamp_png_bytes = generate_signature_stamp(
    signer_name=signer_name,
    document_path=input_pdf_path,
    timestamp=now,
    width_pt=width,   # Ancho real en puntos
    height_pt=height  # Alto real en puntos
)
```

Luego se escala al tamaño exacto en el PDF:

```python
pdf_image = PdfImage(pil_img, box=BoxConstraints(width=width, height=height))
```

## ✅ Validaciones

### Frontend (JavaScript)

| Propiedad | Mínimo | Máximo | Step |
|-----------|--------|--------|------|
| Ancho | 50 pt | 400 pt | 5 pt |
| Alto | 30 pt | 200 pt | 5 pt |
| X | 0 | canvas_width - width | - |
| Y | 0 | canvas_height - height | - |

### Backend (Django/Python)

```python
# En forms.py
x = forms.FloatField(min_value=0)
y = forms.FloatField(min_value=0)
width = forms.FloatField(min_value=10, label='Ancho (puntos)')
height = forms.FloatField(min_value=10, label='Alto (puntos)')
```

## 🔄 Batch Signing (Firma Masiva)

### Reutilización de Configuración

Una vez que se define el tamaño de la firma en un documento:

```javascript
// El tamaño se guarda en los campos del formulario
document.getElementById('id_width').value = 200;
document.getElementById('id_height').value = 50;
```

En firma masiva, estos valores se reutilizan para todos los documentos:

```python
width = form.cleaned_data['width']   # 200 pt
height = form.cleaned_data['height'] # 50 pt

for doc in documents:
    signed_pdf = sign_pdf_service(..., width=width, height=height)
```

### Validación de Compatibilidad

Antes de firmar lotes, se valida que todos los documentos tengan dimensiones similares (variación ±10 puntos):

```python
reference_size = get_pdf_page_size(first_doc, page)
for doc in other_docs:
    size = get_pdf_page_size(doc, page)
    if abs(size[0] - reference_size[0]) > 10 or abs(size[1] - reference_size[1]) > 10:
        raise ValidationError("Dimensiones incompatibles")
```

## 🎯 Casos de Uso

### Caso 1: Firma Individual con Ajuste de Tamaño

1. Usuario navega al PDF y ve la previsualización
2. Hace clic en la ubicación deseada (aparece firma con tamaño por defecto)
3. Arrastra las esquinas para redimensionar
4. Ajusta los valores numéricos si es necesario
5. Desactiva "Mantener proporción" si necesita dimensiones específicas
6. Carga certificado y contraseña
7. Presiona "Firmar Documento"

**Resultado**: PDF con firma exactamente al tamaño especificado

### Caso 2: Firma Masiva Consistente

1. Usuario tiene 50 documentos con espacios de firma similares
2. Abre la interfaz de "Firma Masiva"
3. Define: Página 1, X=50, Y=100, Ancho=180, Alto=45
4. Carga múltiples PDFs, certificado y contraseña
5. Presiona "Firmar Documentos y Descargar ZIP"

**Resultado**: ZIP con 50 PDFs firmados con la misma configuración

### Caso 3: Ajuste Fino de Proporción

1. Usuario tiene un espacio de firma muy específico (ej: 250x30)
2. Activa el toggle "Mantener proporción" antes de cambiar valores
3. Cambia el ancho a 250 → Alto se ajusta automáticamente a 30
4. Procede con la firma

**Resultado**: Firma con proporción exacta mantenida

## 📐 Consideraciones Técnicas

### Precisión Numérica

- Coordenadas se almacenan con **2 decimales** (`toFixed(2)`)
- PyHanko acepta floats y los convierte internamente
- El PDF los almacena con la precisión del sistema PDF

### Performance

- El resize se realiza en tiempo real sin necesidad de renderizar el PDF nuevamente
- Solo se actualizan las propiedades CSS del elemento visual
- Los cálculos de conversión son operaciones matemáticas simples

### Compatibilidad

- Funciona en navegadores modernos que soportan:
  - CSS Grid
  - Event listeners de mouse
  - FileReader API (para PDFs)
- Sin dependencias externas para el resize (puro JavaScript)

## 🐛 Debugging

### El tamaño no se mueve correctamente

**Causa**: Escala incorrecta
**Solución**: Verificar que `scale = 1.4` coincida en JavaScript

### Las firmas aparecen fuera de los bordes

**Causa**: Cálculo de Y incorrecto
**Solución**: Revisar la conversión de coordenadas Y (debe ser invertida)

### Batch signing falla por dimensiones

**Causa**: PDFs con tamaños muy diferentes
**Solución**: Aumentar la tolerancia en `batch_sign` de 10 a 15-20 puntos

## 📝 Cambios Recientes

- ✅ Agregados handles de resize visuales (4 esquinas)
- ✅ Inputs numéricos con validación de rango
- ✅ Toggle para mantener proporción (aspect ratio lock)
- ✅ Previsualización en tiempo real durante drag/resize
- ✅ Mejorada la interfaz de batch signing
- ✅ Documentación técnica completa

## 🚀 Mejoras Futuras (Roadmap)

- [ ] Slider deslizante para tamaño rápido
- [ ] Guardar "presets" de firmastamañorecuentes
- [ ] Visualización de escala actual en %
- [ ] Soporte para rotar la firma (0°, 90°, 180°, 270°)
- [ ] Preview en varias páginas simultáneamente
