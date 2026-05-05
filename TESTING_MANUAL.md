# 🧪 Manual de Testing - Redimensionamiento de Firmas

## 🎯 Objetivo
Verificar que la funcionalidad de redimensionamiento funciona correctamente en tu entorno local.

---

## 📋 Pre-requisitos

- [ ] Docker y Docker Compose instalados
- [ ] Proyecto clonado: `https://github.com/ChaeMendoza/ecuador-pdf-signer`
- [ ] Rama: `main`
- [ ] 30 minutos disponibles

---

## 🚀 Setup Inicial

### Paso 1: Levantar los Contenedores

```bash
cd /home/chae/Proyectos/firma_digital
docker-compose up --build -d
```

Esperar ~30 segundos hasta que esté listo:

```bash
docker-compose logs -f web
# Buscar: "Starting development server at http://0.0.0.0:8000/"
```

### Paso 2: Crear Usuario de Prueba

```bash
docker-compose exec web python manage.py shell

# En el shell interactivo:
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('testuser', 'test@test.com', 'testpass123')
>>> exit()
```

### Paso 3: Acceder a la Aplicación

Abrir navegador: http://localhost:8000

Ingresar con:
- **Usuario**: testuser
- **Contraseña**: testpass123

---

## 📄 Obtener un Certificado de Prueba

Para probar la firma, necesitas un certificado .p12

### Opción A: Usar Certificado Ficticio (Más Fácil)

```bash
# Crear un certificado autofirmado de prueba
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
openssl pkcs12 -export -inkey key.pem -in cert.pem -out test_cert.p12 -passout pass:testpass

# El archivo test_cert.p12 se usará en las pruebas
# Contraseña: testpass
```

### Opción B: Usar un Certificado Real

Si tienes tu certificado digital EC (.p12), simplemente úsalo directamente.

---

## ✅ Test 1: Firma Individual Básica

### Paso 1: Subir un PDF

1. Navegar a **"Documentos"** → **"Nuevo Documento"**
2. Descargar un PDF de prueba:
   ```bash
   # Crear PDF de prueba (A4)
   python -c "
   from reportlab.pdfgen import canvas
   from reportlab.lib.pagesizes import letter
   c = canvas.Canvas('/tmp/test_document.pdf', pagesize=letter)
   c.drawString(100, 750, 'Test Document for Signature')
   c.drawString(100, 700, 'Firme aquí:')
   c.drawRect(100, 680, 250, 50)
   c.save()
   print('PDF creado: /tmp/test_document.pdf')
   "
   ```
3. Seleccionar `/tmp/test_document.pdf`
4. Presionar **"Subir Documento"**
5. ✅ Debe aparecer en la lista

### Paso 2: Colocar Firma (Posición)

1. Hacer clic en el documento subido → **"Firmar Documento"**
2. En el PDF, hacer clic en el área de firma (donde dice "Firme aquí")
3. Debe aparecer un **recuadro azul punteado**
4. El panel derecho debe mostrar:
   ```
   Página: 1
   X: [valor en puntos]
   Y: [valor en puntos]
   ✅ Posición seleccionada
   ```
5. ✅ Posición correcta

---

## ✅ Test 2: Redimensionamiento Visual (Nuevo)

**Requisito:** Haber completado Test 1

### Paso 1: Activar Controles de Tamaño

1. El recuadro de firma debe estar visible
2. Pasar el mouse sobre el recuadro
3. Deben aparecer **4 puntos pequeños** en las esquinas
4. ✅ Handles visibles

### Paso 2: Drag en Esquina SE (Sureste)

1. Hacer clic y arrastrar la esquina **inferior derecha** del recuadro
2. Arrastrar **hacia la derecha** (~50px)
3. Observar:
   - ✅ El recuadro se hace más ancho
   - ✅ En el panel derecho, "Ancho" aumenta
   - ✅ Si "Mantener proporción" está marcado, "Alto" también aumenta

### Paso 3: Drag en Esquina NW (Noroeste)

1. Hacer clic en la esquina **superior izquierda**
2. Arrastrar **hacia la izquierda** (~30px)
3. Observar:
   - ✅ El recuadro se hace más ancho (se mueve izquierda)
   - ✅ Ancho en el panel aumenta
   - ✅ X (posición) también cambia

### Paso 4: Validación de Límites

1. Intentar arrastrar la esquina SE **muy lejos a la derecha**
2. El recuadro debe detenerse **antes de salirse del PDF**
3. ✅ Clamping funciona (no se sale)

---

## ✅ Test 3: Inputs Numéricos (Nuevo)

**Requisito:** Test 1 y 2 completados

### Paso 1: Cambiar Ancho

1. En el panel derecho, ver sección **"Tamaño de Firma"**
2. Campo "Ancho": cambiar valor a **250**
3. Presionar Tab o hacer clic fuera del campo
4. Observar:
   - ✅ El recuadro visual se hace más ancho
   - ✅ Es proporcional (250 / 1.4 ≈ 178px en canvas)

### Paso 2: Cambiar Alto

1. Campo "Alto": cambiar a **60**
2. Presionar Tab
3. Observar:
   - ✅ El recuadro se hace más alto
   - Con "Mantener proporción" ✓: Ancho debe ajustarse también

### Paso 3: Aspect Ratio Lock

1. Dejar "Mantener proporción" **marcado** (✓)
2. Cambiar "Ancho" a **300**
3. Observar:
   - ✅ "Alto" se ajusta automáticamente (300 / proporción)
   - Ej: si proporción es 4:1, Alto será 75

4. **Desmarcar** "Mantener proporción" (☐)
5. Cambiar "Ancho" a **350**
6. Observar:
   - ✅ "Alto" NO cambia
   - Ancho = 350, Alto sigue siendo 75

### Paso 4: Validación de Rango

1. Intentar ingresar "Ancho": **25** (menor que 50)
2. Presionar Tab
3. Observar:
   - ✅ Se ajusta automáticamente a **50**

4. Intentar "Ancho": **500** (mayor que 400)
5. Observar:
   - ✅ Se ajusta a **400**

---

## ✅ Test 4: Firma Individual Completa

**Requisito:** Tests 1-3 completados

### Paso 1: Ajustar Posición y Tamaño

1. Hacer clic nuevamente en el PDF para reubicar la firma
2. Colocarla en una nueva posición
3. Ajustar tamaño con inputs o drag
4. Panel debe mostrar todos los valores correctos

### Paso 2: Cargar Certificado

1. Hacer clic en **"Certificado (.p12 o .pfx)"**
2. Seleccionar `test_cert.p12` (o tu certificado real)
3. Campo "Contraseña": ingresar **testpass** (o tu contraseña)

### Paso 3: Firmar Documento

1. Presionar botón **"Firmar Documento"**
2. El botón debe mostrar estado "Firmando PDF..."
3. Esperar ~5-10 segundos
4. Observar:
   - ✅ Éxito: Redirige a lista de documentos
   - ✅ Documento ahora muestra status "Firmado"
   - ✅ Botón "Descargar PDF Firmado" disponible

### Paso 4: Verificar Firma

1. Presionar **"Descargar PDF Firmado"**
2. Abrir el PDF con un lector (ej: Adobe Reader, Foxit)
3. Observar:
   - ✅ Tiene 1 página (igual que original)
   - ✅ Muestra la firma con el QR + información
   - ✅ La firma está en el tamaño especificado
   - ✅ La firma está en la posición especificada

---

## ✅ Test 5: Firma Masiva (Nuevo)

**Requisito:** Tener 2-3 PDFs de prueba con el mismo tamaño

### Paso 1: Preparar PDFs

```bash
# Crear 3 PDFs idénticos (A4)
for i in 1 2 3; do
  python -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
c = canvas.Canvas('/tmp/test_$i.pdf', pagesize=letter)
c.drawString(100, 750, 'Test Document $i')
c.save()
"
done
```

### Paso 2: Acceder a Firma Masiva

1. Navegar a **"Documentos"** → **"Firma Masiva"**
2. Debe verse formulario con:
   - ✅ Selector de documentos (múltiples)
   - ✅ Campos de Posición (Página, X, Y)
   - ✅ Campos de Tamaño (Ancho, Alto) - NUEVO
   - ✅ Certificado y contraseña

### Paso 3: Configurar Parámetros

1. **Documentos**: Seleccionar test_1.pdf, test_2.pdf, test_3.pdf
2. **Posición**:
   - Página: 1
   - X: 50
   - Y: 100
3. **Tamaño**:
   - Ancho: 200
   - Alto: 50
4. **Certificado**: test_cert.p12
5. **Contraseña**: testpass

### Paso 4: Procesar Batch

1. Presionar **"Firmar Documentos y Descargar ZIP"**
2. Esperar ~15-20 segundos (depende de cantidad)
3. Debe descargar archivo **"signed_documents.zip"**

### Paso 5: Verificar ZIP

```bash
# Extraer ZIP
unzip -l ~/Downloads/signed_documents.zip

# Debe mostrar:
# signed_test_1.pdf
# signed_test_2.pdf
# signed_test_3.pdf

# Extraer y verificar un PDF
unzip ~/Downloads/signed_documents.zip
open signed_test_1.pdf
```

Observar:
- ✅ 3 PDFs con firma
- ✅ Cada uno con tamaño **200x50** pt
- ✅ Posición en **X=50, Y=100**
- ✅ Firma correctamente escalada

---

## ✅ Test 6: Validaciones y Edge Cases

### Test 6A: Dimensiones Incompatibles en Batch

1. Crear 2 PDFs con tamaños diferentes:
   ```bash
   # A4 (595x842)
   # Carta (612x792)
   ```
2. Intentar firmar batch con ambos
3. Debe mostrar error:
   ```
   ❌ "Dimensiones incompatibles..."
   ```
4. ✅ Validación funciona

### Test 6B: Límite de 100 Documentos

1. Intentar seleccionar >100 PDFs
2. Debe mostrar error en la vista
3. ✅ No procesa

### Test 6C: Firma se Sale del Documento

1. Establecer X = 500, Y = 500, Ancho = 500, Alto = 500 (valores grandes)
2. Hacer clic en PDF
3. Observar:
   - ✅ El recuadro se ajusta automáticamente
   - ✅ No se sale de los bordes

---

## 🐛 Checklist de Debugging

Si algo no funciona:

### Consola del Navegador (F12)

```javascript
// Verificar escalas
console.log(`Scale: ${scale}`);
console.log(`Signature Size: ${SIGNATURE_WIDTH_PT}x${SIGNATURE_HEIGHT_PT}`);

// Verificar eventos
// Abrir consola y verificar logs de drag
```

### Logs de Docker

```bash
# Ver logs del web
docker-compose logs -f web

# Buscar errores de "Signature" o "sign_pdf"
```

### Base de Datos

```bash
# Verificar que los valores se guardaron
docker-compose exec web python manage.py shell

>>> from apps.documents.models import Document
>>> d = Document.objects.last()
>>> print(f"Width: {d.signature_width}, Height: {d.signature_height}")
```

---

## 📊 Matriz de Validación

Marcar ✅ conforme completes:

| Área | Test | ✅ |
|------|------|-----|
| **Setup** | Docker up | |
| | Usuario creado | |
| **Test 1** | Subir PDF | |
| | Posición | |
| **Test 2** | Handles visibles | |
| | Drag SE | |
| | Drag NW | |
| | Límites respetados | |
| **Test 3** | Ancho editable | |
| | Alto editable | |
| | Aspect ratio lock | |
| | Validación rango | |
| **Test 4** | Firma completa | |
| | PDF descargable | |
| | PDF verificable | |
| **Test 5** | Batch seleccionar | |
| | Batch procesar | |
| | ZIP descargable | |
| | PDFs verificables | |
| **Test 6** | Validaciones | |
| | Edge cases | |

---

## 🎉 Resultado

Si todos los tests pasan: **✅ FUNCIONALIDAD LISTA PARA PRODUCCIÓN**

---

## 📞 Soporte

Si encuentras problemas:

1. Revisar [TEST_PLAN.md](TEST_PLAN.md) para casos esperados
2. Consultar [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) para detalles técnicos
3. Ver [QUICKSTART.md](QUICKSTART.md) para setup
4. Revisar logs de Docker: `docker-compose logs web`

---

**Tiempo estimado:** 30 minutos

**Última actualización:** 5 de mayo de 2026
