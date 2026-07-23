# Standalone PDF Signer

Este paquete es un módulo independiente de Python extraído de la lógica original del proyecto de firma digital en Ecuador. Está diseñado para firmar documentos PDF digitalmente utilizando certificados PKCS#12 (`.p12` o `.pfx`) y generar una estampa de firma visible al estilo de la aplicación oficial **FirmaEC** (código QR a la izquierda y metadatos legibles a la derecha).

Es completamente **independiente de Django** y se puede integrar fácilmente con lenguajes externos como Node.js (por ejemplo, en AdonisJS v6), PHP, Ruby o Go mediante la ejecución de su interfaz de consola (CLI).

---

## 📋 Requisitos e Instalación

Para utilizar este paquete, debes contar con **Python 3.11+** y las librerías del sistema necesarias para compilar dependencias criptográficas y de procesamiento de imágenes.

### 1. Clonar/Copiar la carpeta
Asegúrate de tener la carpeta `standalone_signer/` en tu entorno de despliegue.

### 2. Crear entorno virtual (Recomendado)
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

Las dependencias principales son:
* **pyHanko** (con soporte de imágenes): Para aplicar la firma criptográfica incremental sobre el PDF.
* **cryptography**: Para desencriptar los archivos PKCS#12 y validar credenciales.
* **Pillow**: Para la generación y manipulación de la imagen de estampa.
* **qrcode**: Para la generación dinámica del código QR insertado en la firma.

---

## 🚀 Uso del CLI (Línea de comandos)

El paquete incluye el script `cli.py` para invocarlo directamente desde la consola:

```bash
python cli.py \
  --input certificado.pdf \
  --output firmado.pdf \
  --certificate certificado.p12 \
  --password "contraseña_del_certificado" \
  --page 1 \
  --x 50 \
  --y 50 \
  --width 250 \
  --height 60
```

### Parámetros del CLI:
* `--input` (Obligatorio): Ruta al archivo PDF original.
* `--output` (Obligatorio): Ruta donde se guardará el PDF firmado.
* `--certificate` (Obligatorio): Ruta al certificado PKCS#12 (`.p12` o `.pfx`).
* `--password` (Obligatorio): Contraseña del certificado.
* `--page` (Opcional): Número de página para estampar la firma (1-indexed). Por defecto es `1`.
* `--x` (Opcional): Coordenada horizontal (en puntos PDF) para la esquina inferior izquierda de la firma. Por defecto es `50`.
* `--y` (Opcional): Coordenada vertical (en puntos PDF) para la esquina inferior izquierda de la firma. Por defecto es `50`.
* `--width` (Opcional): Ancho de la estampa de firma en puntos PDF. Por defecto es `250`.
* `--height` (Opcional): Alto de la estampa de firma en puntos PDF. Por defecto es `60`.

### Códigos de salida (Exit codes):
* `0`: Operación exitosa.
* `1`: Error controlado de validación de firma (por ejemplo, contraseña incorrecta o página fuera de rango). Mensaje detallado en `stderr`.
* `2`: Error inesperado del sistema.

---

## 🐍 Uso de la API en Python

También puedes importar la funcionalidad directamente en tus propios desarrollos de Python:

```python
from signer import PdfSigner
from signer.exceptions import InvalidPasswordError, SignerError

signer = PdfSigner()

try:
    signer.sign(
        input_pdf="documento.pdf",
        output_pdf="documento_firmado.pdf",
        certificate="firma.p12",
        password="mi_contrasena",
        page=1,
        x=50,
        y=100,
        width=250,
        height=60
    )
    print("Firma realizada con éxito!")
except InvalidPasswordError:
    print("La contraseña del certificado es incorrecta.")
except SignerError as e:
    print(f"Error de firma: {e}")
```

---

## 🟢 Integración con Node.js / AdonisJS v6

En AdonisJS v6, puedes utilizar la librería **execa** (recomendado para subprocesos) o el módulo nativo **child_process** de Node.js para ejecutar el CLI y manejar la firma de manera asíncrona.

### Ejemplo con `execa` (Recomendado)

```javascript
import { execa } from 'execa'
import { join } from 'path'

async function firmarPdf(inputPdf, outputPdf, certPath, password, opts = {}) {
  const cliPath = join(process.cwd(), 'standalone_signer/cli.py')
  const pythonPath = join(process.cwd(), 'standalone_signer/venv/bin/python') // Ruta al binario de Python del venv

  const args = [
    cliPath,
    '--input', inputPdf,
    '--output', outputPdf,
    '--certificate', certPath,
    '--password', password,
    '--page', (opts.page || 1).toString(),
    '--x', (opts.x || 50).toString(),
    '--y', (opts.y || 50).toString(),
    '--width', (opts.width || 250).toString(),
    '--height', (opts.height || 60).toString(),
  ]

  try {
    const { stdout } = await execa(pythonPath, args)
    console.log('Salida:', stdout)
    return { success: true, message: 'Archivo firmado exitosamente.', outputPdf }
  } catch (error) {
    // Si el proceso de Python retorna un código diferente a 0
    console.error('Error al firmar PDF:', error.stderr || error.message)
    return { 
      success: false, 
      message: error.stderr ? error.stderr.trim() : 'Error interno en la firma.' 
    }
  }
}
```

### Ejemplo con `child_process` nativo (sin dependencias adicionales)

```javascript
const { execFile } = require('child_process');
const path = require('path');

function firmarPdfNativo(inputPdf, outputPdf, certPath, password, opts = {}) {
  return new Promise((resolve, reject) => {
    const cliPath = path.join(__dirname, 'standalone_signer/cli.py');
    const pythonPath = path.join(__dirname, 'standalone_signer/venv/bin/python');

    const args = [
      cliPath,
      '--input', inputPdf,
      '--output', outputPdf,
      '--certificate', certPath,
      '--password', password,
      '--page', (opts.page || 1).toString(),
      '--x', (opts.x || 50).toString(),
      '--y', (opts.y || 50).toString(),
      '--width', (opts.width || 250).toString(),
      '--height', (opts.height || 60).toString(),
    ];

    execFile(pythonPath, args, (error, stdout, stderr) => {
      if (error) {
        console.error('Error de firma:', stderr || error.message);
        return resolve({ success: false, message: stderr ? stderr.trim() : error.message });
      }
      console.log('Éxito:', stdout);
      resolve({ success: true, message: stdout.trim(), outputPdf });
    });
  });
}
```
