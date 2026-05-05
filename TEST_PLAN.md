# ✅ Plan de Pruebas - Redimensionamiento de Firmas

## 🎯 Objetivos de Prueba

Validar que:
1. El redimensionamiento visual funciona correctamente
2. Las coordenadas se convierten correctamente entre canvas y PDF
3. Las validaciones previenen errores
4. El batch signing reutiliza la configuración
5. La firma se aplica con las dimensiones exactas especificadas

---

## 🧪 Pruebas Unitarias (Backend)

### Test: Validación de Formulario
```python
def test_sign_document_form_valid():
    """Verificar que el formulario acepta coordenadas válidas."""
    form = SignDocumentForm(data={
        'p12_file': 'test.p12',
        'password': 'test123',
        'page': 1,
        'x': 50.5,
        'y': 100.2,
        'width': 200.0,
        'height': 50.0,
    })
    assert form.is_valid()
    assert form.cleaned_data['width'] == 200.0
    assert form.cleaned_data['height'] == 50.0
```

### Test: Batch Signing Valida Dimensiones
```python
def test_batch_sign_incompatible_dimensions():
    """Verificar que rechaza PDFs con dimensiones diferentes."""
    # Crear dos PDFs: uno A4 (595x842) y otro Letter (612x792)
    doc1 = create_test_pdf(width=595, height=842)  # A4
    doc2 = create_test_pdf(width=612, height=792)  # Letter
    
    response = client.post('/documents/batch-sign/', {
        'documents': [doc1, doc2],
        'page': 1,
        'x': 50,
        'y': 50,
        'width': 200,
        'height': 50,
        'p12_file': 'cert.p12',
        'password': 'pass',
    })
    
    assert response.status_code == 302  # Redirect con error
    assert 'Dimensiones incompatibles' in messages
```

### Test: Firma Recibe Dimensiones Correctas
```python
def test_sign_pdf_service_with_custom_size():
    """Verificar que sign_pdf_service respeta las dimensiones."""
    signed_path = sign_pdf_service(
        'original.pdf',
        p12_content,
        password,
        page=1,
        x=50, y=100,
        width=250,  # Custom width
        height=60,   # Custom height
    )
    
    # Leer el PDF firmado y verificar que tiene el campo de firma
    from pyhanko.pdf_utils.reader import PdfFileReader
    with open(signed_path, 'rb') as f:
        reader = PdfFileReader(f)
        fields = reader.get_form_fields()
        
        # Buscar campo 'FirmaDigital'
        assert 'FirmaDigital' in fields
        sig_field = fields['FirmaDigital']
        
        # Verificar coordenadas
        assert sig_field.width == 250
        assert sig_field.height == 60
```

---

## 🎨 Pruebas de Frontend (JavaScript)

### Test: Drag & Resize en Esquinas
```javascript
describe('Signature Box Resizing', () => {
    test('Resize NE corner increases width', () => {
        // Simular drag en esquina NE
        const initialWidth = signatureBox.offsetWidth;
        simulateDrag(
            document.querySelector('[data-handle="ne"]'),
            {dx: 50, dy: -20}
        );
        
        // Ancho debe aumentar, alto debe disminuir
        expect(signatureBox.offsetWidth).toBeGreaterThan(initialWidth);
    });
    
    test('Aspect ratio lock maintains proportion', () => {
        aspectRatioLock.checked = true;
        
        const initialRatio = signatureBox.offsetWidth / signatureBox.offsetHeight;
        
        simulateDrag(
            document.querySelector('[data-handle="se"]'),
            {dx: 40, dy: 0}
        );
        
        const newRatio = signatureBox.offsetWidth / signatureBox.offsetHeight;
        expect(newRatio).toBeCloseTo(initialRatio, 2);
    });
    
    test('Signature box stays within canvas boundaries', () => {
        const canvas = document.getElementById('pdf-render');
        simulateDrag(
            document.querySelector('[data-handle="se"]'),
            {dx: 10000, dy: 10000}  // Drag fuera de límites
        );
        
        // Verificar que no se sale del canvas
        expect(signatureBox.offsetLeft + signatureBox.offsetWidth)
            .toBeLessThanOrEqual(canvas.width);
        expect(signatureBox.offsetTop + signatureBox.offsetHeight)
            .toBeLessThanOrEqual(canvas.height);
    });
});
```

### Test: Inputs Numéricos
```javascript
describe('Size Inputs', () => {
    test('Width input updates signature box', () => {
        widthInput.value = 250;
        widthInput.dispatchEvent(new Event('change'));
        
        expect(signatureBox.offsetWidth).toBe(250 * scale);
        expect(document.getElementById('id_width').value).toBe('250');
    });
    
    test('Height input with aspect ratio lock', () => {
        aspectRatioLock.checked = true;
        const initialRatio = SIGNATURE_WIDTH_PT / SIGNATURE_HEIGHT_PT;
        
        heightInput.value = 60;
        heightInput.dispatchEvent(new Event('change'));
        
        const newRatio = SIGNATURE_WIDTH_PT / SIGNATURE_HEIGHT_PT;
        expect(newRatio).toBeCloseTo(initialRatio, 2);
    });
    
    test('Inputs validate min/max ranges', () => {
        widthInput.value = 25;  // Menor que 50
        widthInput.dispatchEvent(new Event('change'));
        
        expect(SIGNATURE_WIDTH_PT).toBeGreaterThanOrEqual(50);
    });
});
```

### Test: Conversión Canvas ↔ PDF
```javascript
describe('Coordinate Conversion', () => {
    test('Canvas to PDF conversion', () => {
        // Posicionar firma en canvas
        signatureBox.style.left = '140px';  // 140 / 1.4 = 100 pt
        signatureBox.style.top = '70px';
        
        updateFormFieldsFromBox();
        
        const pdfX = parseFloat(document.getElementById('id_x').value);
        expect(pdfX).toBeCloseTo(100, 0);
    });
    
    test('PDF to Canvas inverse conversion', () => {
        // Si X = 100 pt en PDF, en canvas debe ser 140px
        const pdfX = 100;
        const canvasX = pdfX * scale;  // 140
        
        expect(canvasX).toBe(140);
    });
    
    test('Y coordinate inversion', () => {
        // En PDF: Y=0 está abajo, en canvas: Y=0 está arriba
        const canvasHeight = 1000;
        const pdfY = 100;
        const signatureHeight = 50;
        
        const canvasY = (canvasHeight / scale) - pdfY - signatureHeight;
        // canvas_y debe ser diferente de pdf_y
        expect(canvasY).not.toBe(pdfY);
    });
});
```

---

## 🎬 Pruebas de Integración

### Test: Flujo Completo de Firma Individual

**Precondiciones:**
- Usuario autenticado
- PDF subido (ej: document.pdf)

**Pasos:**

```gherkin
Escenario: Firmar documento con tamaño personalizado

Dado que tengo un documento PDF subido
Y me encuentro en la página "Firmar Documento"

Cuando hago clic en la posición (200, 300) del PDF
Entonces debe aparecer un recuadro azul en esa posición

Cuando arrastro la esquina SE del recuadro 50px a la derecha
Entonces el recuadro debe ampliarse
Y los inputs "Ancho" y "Alto" deben actualizarse

Cuando cambio el "Ancho" a 250 en el input
Y el checkbox "Mantener proporción" está marcado
Entonces el "Alto" debe ajustarse proporcionalmente

Cuando subo mi certificado (cert.p12)
Y ingreso mi contraseña
Y presiono "Firmar Documento"

Entonces el PDF debe descargarse con el nombre "signed_document.pdf"
Y el documento en la BD debe tener:
  - status = 'signed'
  - signature_width = 250
  - signature_height = 62.5 (aprox, según proporción)
```

### Test: Flujo de Firma Masiva

**Precondiciones:**
- Usuario autenticado

**Pasos:**

```gherkin
Escenario: Firmar múltiples documentos con mismo tamaño

Dado que tengo 5 PDFs con formato A4
Y me encuentro en "Firma Masiva de Documentos"

Cuando selecciono los 5 PDFs
Y establezco:
  - Página: 1
  - Posición X: 50, Y: 100
  - Tamaño: 200x50
Y subo certificado y contraseña
Y presiono "Firmar Documentos y Descargar ZIP"

Entonces debo descargar un archivo "signed_documents.zip"
Y el ZIP debe contener 5 PDFs:
  - signed_doc1.pdf
  - signed_doc2.pdf
  - signed_doc3.pdf
  - signed_doc4.pdf
  - signed_doc5.pdf

Y cada PDF debe tener la firma con tamaño 200x50 en la posición (50, 100)
```

---

## 📋 Casos de Prueba Manual

### Caso 1: Resize Interactivo
```
[ ] 1. Cargar un PDF en documento_sign
[ ] 2. Hacer clic en el PDF → aparece recuadro azul
[ ] 3. Pasar mouse sobre recuadro → aparecen puntos en esquinas
[ ] 4. Arrastra esquina SE → firma se agranda
[ ] 5. Arrastra esquina NW → firma se empequeñece
[ ] 6. Los inputs numéricos se actualizan en tiempo real
[ ] 7. Mantener dentro de los límites (no se sale del PDF)
```

### Caso 2: Inputs Numéricos
```
[ ] 1. Hacer clic para colocar firma
[ ] 2. En el panel derecho, cambiar "Ancho" a 150
[ ] 3. La firma visual se redimensiona a 150 / 1.4 ≈ 107px
[ ] 4. Con "Mantener proporción" activado, cambiar "Alto" a 75
[ ] 5. El "Ancho" debe ajustarse (150 * 75/50 = 225)
[ ] 6. Desactivar "Mantener proporción"
[ ] 7. Cambiar "Ancho" sin que se altere el "Alto"
```

### Caso 3: Batch Signing
```
[ ] 1. Ir a "Firma Masiva"
[ ] 2. Seleccionar 3 PDFs (mismas dimensiones)
[ ] 3. Establecer tamaño 200x50
[ ] 4. Hacer submit
[ ] 5. Descargar ZIP
[ ] 6. Extraer ZIP y abrir cada PDF
[ ] 7. Verificar que cada firma tiene 200x50 pt
[ ] 8. Intentar con 2 PDFs de diferentes tamaños
[ ] 9. Debe mostrar error "Dimensiones incompatibles"
```

### Caso 4: Validación de Límites
```
[ ] 1. Intentar ingresar ancho = 25 (menor que 50)
[ ] 2. Sistema debe ajustar a 50
[ ] 3. Intentar ancho = 500 (mayor que 400)
[ ] 4. Sistema debe ajustar a 400
[ ] 5. Intentar altura = 10 (menor que 30)
[ ] 6. Sistema debe ajustar a 30
[ ] 7. Intentar altura = 300 (mayor que 200)
[ ] 8. Sistema debe ajustar a 200
```

---

## 🔍 Pruebas de Compatibilidad

### Navegadores
```
[ ] Chrome 125+
[ ] Firefox 122+
[ ] Safari 17+
[ ] Edge 125+
```

### PDFs
```
[ ] PDF estándar (sin encripción)
[ ] PDF con múltiples páginas
[ ] PDF A4 (595x842 pt)
[ ] PDF Carta (612x792 pt)
[ ] PDF personalizado (100x100 pt)
```

### Dispositivos
```
[ ] Desktop (1920x1080)
[ ] Tablet (768x1024)
[ ] Mobile (375x667) - responsivo
```

---

## 📊 Resultados Esperados

### Antes de la mejora
```
- Tamaño fijo 200x50 pt
- Solo control visual de posición
- Sin validación interactiva
- Difícil adaptar a espacios variables
```

### Después de la mejora ✅
```
✓ Tamaño configurable (50-400 x 30-200 pt)
✓ Control interactivo: drag, inputs numéricos
✓ Aspect ratio lock opcional
✓ Validación en tiempo real
✓ Reutilización en batch signing
✓ Previsualización precisa
```

---

## 🚨 Bugs Conocidos a Verificar

| Bug | Solución | Estado |
|-----|----------|--------|
| Escala incorrecta en zoom | Usar `getBoundingClientRect()` | ✅ Fixed |
| Y invertida al cambiar página | Recalcular en renderPage | ✅ Fixed |
| Aspect ratio no se mantiene | Guardar ratio inicial | ✅ Fixed |
| Box se sale en cantos | Clamping en mousemove | ✅ Fixed |
| Width/height no actualizan form | Llamar updateFormFields() | ✅ Fixed |

---

## 📈 Performance

Medir:
```
- Tiempo de drag responsiveness: < 16ms (60 FPS)
- Cálculo de conversión: < 1ms
- Renderizado PDF: < 2s (depende de tamaño)
- Tiempo de firma: < 5s
```

---

## ✨ Checklists de Validación

### Antes de Hacer Deploy

- [ ] Todas las pruebas unitarias pasan
- [ ] Todas las pruebas de integración pasan
- [ ] Sin errores en consola (F12)
- [ ] Sin warnings de JavaScript
- [ ] Responsivo en mobile
- [ ] Certificado se destruye correctamente
- [ ] No hay fugas de memoria en drag/resize
- [ ] Batch signing funciona con 100 documentos
- [ ] Documentación actualizada
- [ ] README incluye instrucciones de uso nuevo

### Después de Deploy

- [ ] Verificar en producción
- [ ] Monitorear errores en logs
- [ ] Recopilar feedback de usuarios
- [ ] Perfil de rendimiento en navegadores reales
- [ ] A/B test si aplica

---

**Última actualización**: 5 de mayo de 2026  
**Responsable**: Equipo QA
