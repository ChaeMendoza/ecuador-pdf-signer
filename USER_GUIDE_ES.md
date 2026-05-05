# 📖 Guía de Usuario - Redimensionamiento de Firmas

## 🎯 Funcionalidad Nueva

Ahora puedes **ajustar el tamaño de la firma** antes de aplicarla en tus documentos PDF. Esto es especialmente útil cuando:

- Los espacios de firma varían entre documentos
- Necesitas que la firma sea más pequeña o más grande
- Quieres reutilizar las mismas dimensiones en lotes de documentos

## 📱 Firma Individual de Documentos

### Paso 1: Cargar el Documento
1. Entra a **"Documentos"** → **"Firmar Documento"** en el documento deseado
2. Se mostrará una vista previa del PDF con controles de navegación

### Paso 2: Seleccionar Posición
1. **Haz clic en el PDF** donde deseas colocar la firma
2. Aparecerá un **recuadro azul** que indica la ubicación
3. El panel derecho mostrará:
   - Página seleccionada
   - Posición X e Y en puntos (pt)
   - Botón "Posición seleccionada" en verde

### Paso 3: Ajustar Tamaño (NUEVO ⭐)

#### Opción A: Arrastrando las Esquinas
```
    1. Pasa el mouse sobre el recuadro azul
    2. Verás puntos pequeños en las 4 esquinas
    3. Arrastra cualquier esquina para redimensionar
    
    Comportamiento:
    ✓ La firma se redimensiona en tiempo real
    ✓ Se respeta la proporción si está activada
    ✓ La firma siempre queda dentro del documento
```

#### Opción B: Inputs Numéricos
```
En el panel "Tamaño de Firma":

Ancho:  [_____] pt    (mínimo 50, máximo 400)
Alto:   [_____] pt    (mínimo 30, máximo 200)

✓ Mantener proporción [checkbox]
```

**Cómo funciona:**
- Escribe el ancho y/o alto deseados en puntos (pt)
- Si "Mantener proporción" está marcado:
  - Al cambiar el ancho → el alto se ajusta automáticamente
  - Al cambiar el alto → el ancho se ajusta automáticamente
- Si lo desactivas, puedes establecer valores independientes

### Paso 4: Cargar Certificado
1. **Certificado (.p12 o .pfx)**: Selecciona tu archivo digital
2. **Contraseña**: Ingresa la contraseña del certificado
3. ⚠️ Seguridad: Se encripta en tránsito y **NO se almacena** en la base de datos

### Paso 5: Firmar
Presiona **"Firmar Documento"** 
- Se firmará con exactamente el tamaño que especificaste
- La firma incluirá QR + datos del signer + timestamp

---

## 📦 Firma Masiva de Documentos

Ideal para firmar múltiples documentos con la misma posición y tamaño.

### Paso 1: Acceder a Firma Masiva
1. Ve a **"Documentos"** → **"Firma Masiva"**

### Paso 2: Configurar Parámetros
Completa los campos en la sección **"Posición de Firma"** y **"Tamaño de Firma"**:

```
┌─────────────────────────────┐
│ Posición de Firma           │
├─────────────────────────────┤
│ Página:  [1]                │
│ X:       [50]               │
│ Y:       [100]              │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Tamaño de Firma             │
├─────────────────────────────┤
│ Ancho:   [200] pt           │
│ Alto:    [50] pt            │
│                             │
│ 💡 Consejo: Ajusta el       │
│ tamaño para que se adapte   │
│ a los espacios de firma     │
│ en tus documentos.          │
└─────────────────────────────┘
```

### Paso 3: Seleccionar Documentos
Haz clic en **"Documentos PDF"** y selecciona múltiples archivos:
- Pueden ser de diferentes carpetas
- Máximo 100 documentos por lote
- Solo se aceptan archivos `.pdf`

### Paso 4: Certificado y Contraseña
Igual que en firma individual:
- Sube tu certificado `.p12` o `.pfx`
- Ingresa tu contraseña

### Paso 5: Firmar y Descargar
Presiona **"Firmar Documentos y Descargar ZIP"**
- Se procesan todos los archivos
- Se descargan en un archivo `.zip`
- Cada PDF viene con nombre: `signed_original_name.pdf`

---

## ⚙️ Entendiendo los Parámetros

### ¿Qué es "pt" (Punto)?
- **Unidad estándar de PDF**, equivalente a 1/72 pulgadas
- No cambia según el zoom de la pantalla
- Independiente del dispositivo

### Rango de Valores Permitidos

| Parámetro | Mínimo | Máximo | Recomendado |
|-----------|--------|--------|-------------|
| **Ancho** | 50 pt | 400 pt | 150-250 pt |
| **Alto** | 30 pt | 200 pt | 40-80 pt |
| **X** | 0 | ancho_página | Depende |
| **Y** | 0 | alto_página | Depende |

### Cálculo de Dimensiones de Página

**Tamaño A4** (estándar):
- Ancho: 595 pt (210 mm)
- Alto: 842 pt (297 mm)

Para firmar en una A4, ejemplo válido:
- X: 50 pt (margen izquierdo)
- Y: 50 pt (desde abajo)
- Ancho: 200 pt (suficiente espacio)
- Alto: 50 pt (firma compacta)

---

## 💡 Consejos y Trucos

### ✅ Lo Mejor
- ✓ Probar en un documento primero antes de firma masiva
- ✓ Usar "Mantener proporción" para firmas consistentes
- ✓ Documentar qué tamaño funcionó bien (para reutilizar)
- ✓ Verificar que la firma no se salga de los bordes

### ❌ Evitar
- ✗ Firmas muy pequeñas (< 60 pt ancho) - difícil de verificar
- ✗ Firmas que toquen los bordes del documento
- ✗ Cambios bruscos entre documentos (variar más de 50 pt)
- ✗ Usar valores erráticos sin validar primero

### 🎨 Tamaños Recomendados

**Pequeña** (discreta)
- Ancho: 120 pt
- Alto: 35 pt
- Uso: Espacios limitados

**Mediana** (estándar)
- Ancho: 200 pt
- Alto: 50 pt  
- Uso: Mayoría de casos

**Grande** (visible)
- Ancho: 280 pt
- Alto: 70 pt
- Uso: Documentos de importancia

---

## 🔒 Seguridad

- **Tu certificado** nunca se almacena en nuestros servidores
- **La contraseña** solo se usa en memoria durante la firma
- Se envía por **HTTPS** (conexión encriptada)
- Los certificados se destruyen después de firmar
- No hay logs de contraseñas

---

## 🆘 Solución de Problemas

### La firma no aparece donde la puse

**Problema**: Las coordenadas pueden ser incorrectas si cambias de página

**Solución**: 
1. Especifica correctamente la **página** en los controles
2. Recuerda que la firma solo aparece en esa página
3. Verifica que X,Y estén dentro del rango de la página

### El recuadro de la firma se sale del documento

**Problema**: Posición + Tamaño > Dimensiones de página

**Solución**:
1. Reduce el tamaño de la firma
2. Mueve la firma más hacia el centro
3. Usa la previsualización para validar antes de firmar

### "Dimensiones incompatibles" en firma masiva

**Problema**: Los documentos tienen tamaños diferentes

**Solución**:
1. Asegúrate que todos sean A4 (o mismo formato)
2. Si están en formatos diferentes, agrupa por tipo
3. Realiza lotes separados por formato

### El tamaño no se actualiza en los inputs

**Problema**: JavaScript no se ejecutó correctamente

**Solución**:
1. Recarga la página (Ctrl+F5 o Cmd+Shift+R)
2. Borra el caché del navegador
3. Intenta en otro navegador

---

## 📞 Contacto y Soporte

Si tienes problemas adicionales:
1. Verifica que tu navegador sea actualizado
2. Intenta en un navegador diferente
3. Revisa que los PDFs no estén dañados
4. Contacta al administrador del sistema

---

## ✨ Novedades (v2.0)

- ✅ Redimensionamiento visual con drag handles
- ✅ Inputs numéricos para precisión
- ✅ Aspect ratio lock (mantener proporción)
- ✅ Validación en tiempo real
- ✅ Previsualización mejorada
- ✅ Interfaz responsive (móvil-friendly)
