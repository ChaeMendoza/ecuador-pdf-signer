# Sistema Web para Firma Electrónica de PDFs

Un sistema web simple y moderno desarrollado en **Django** para la firma digital de documentos PDF utilizando certificados digitales **.p12** o **.pfx**. Implementa un flujo seguro en el que los certificados y las contraseñas no se almacenan en la base de datos ni permanentemente en el disco.

## 🚀 Tecnologías Principales

*   **Backend:** Python 3.11, Django 5.x
*   **Firma Digital:** `pyHanko`
*   **Base de Datos:** PostgreSQL 15
*   **Infraestructura:** Docker & Docker Compose

## ✨ Funcionalidades

1.  **Autenticación de Usuarios:** Registro seguro e inicio de sesión.
2.  **Gestión de Documentos:** Subida de archivos PDF y visualización de documentos previamente cargados.
3.  **Firma Digital (PAdES):** 
    *   Firma de documentos PDF utilizando certificados `.p12` cargados al vuelo.
    *   Sello visible de validación inyectado en el archivo firmado.
    *   Procesamiento 100% en memoria/temporal (el certificado se destruye inmediatamente tras generar la firma).
    *   **[NUEVO] ⭐ Redimensionamiento interactivo de la firma** antes de aplicarla:
        - Drag & drop en esquinas para ajustar tamaño visualmente
        - Inputs numéricos para control preciso
        - Aspect ratio lock (mantener proporción)
        - Previsualización en tiempo real
4.  **Firma Masiva:** 
    *   Firma múltiples documentos PDF con la misma posición de firma.
    *   Validación de dimensiones similares entre documentos.
    *   Descarga de todos los documentos firmados en un archivo ZIP.
    *   Límite de 100 documentos por lote.
    *   **[NUEVO] ⭐ Reutilización de configuración de tamaño** en lotes

## 🛠️ Requisitos Previos

Asegúrate de tener instalados en tu sistema:
*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

## ⚙️ Instalación y Configuración

1.  **Clonar el repositorio**
    ```bash
    git clone https://github.com/tu-usuario/firma-digital.git
    cd firma-digital
    ```

2.  **Configurar Variables de Entorno**
    El proyecto requiere un archivo `.env` en la raíz. Puedes tomar de base el entorno predeterminado:
    ```env
    POSTGRES_DB=firma_db
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    SECRET_KEY=django-insecure-super-secret-key
    DEBUG=True
    ```

3.  **Levantar el entorno con Docker**
    Construye e inicializa la base de datos y el servidor web:
    ```bash
    docker-compose up --build -d
    ```
    *Nota: Las migraciones de base de datos se aplicarán automáticamente gracias a la configuración del contenedor.*

4.  **Acceso al Sistema**
    *   Abre tu navegador y ve a: `http://localhost:8000`
    *   Para ingresar, simplemente regístrate creando un usuario nuevo en la plataforma.

## 🛡️ Estructura del Proyecto

*   **`apps/`**: Módulos lógicos del sistema.
    *   **`users/`**: Vistas y flujos de autenticación.
    *   **`documents/`**: Modelo `Document` y manejo de la carga de archivos.
    *   **`signing/`**: Servicio de criptografía encargado de aplicar `pyHanko`.
*   **`config/`**: Archivos de configuración principal de Django.
*   **`templates/`**: Estructura frontend minimalista con plantillas base.

## 📚 Documentación

Para información detallada sobre las características:

- **[📖 Guía de Usuario](USER_GUIDE_ES.md)** - Cómo usar el sistema desde la interfaz
- **[⚙️ Documentación Técnica](BACKEND_DOCUMENTATION.md)** - Detalles internos y API
- **[🔧 Guía de Redimensionamiento](SIGNATURE_SIZING_GUIDE.md)** - Cómo funciona el resize interactivo
- **[✅ Plan de Pruebas](TEST_PLAN.md)** - Casos de prueba y validación
- **[🚀 Quick Start](QUICKSTART.md)** - Inicio rápido para desarrolladores
- **[📋 Resumen de Implementación](IMPLEMENTATION_SUMMARY.md)** - Cambios realizados en v2.0
- **[🧪 Testing Manual](TESTING_MANUAL.md)** - Pruebas paso a paso en tu entorno local

## 🤝 Contribuciones

Si deseas mejorar el proyecto, siéntete libre de hacer un _fork_ y abrir un _Pull Request_. Todas las contribuciones son bienvenidas.

## 🎯 Versión 2.0 - Novedades

### ✨ Nueva Funcionalidad: Redimensionamiento de Firmas

#### Características Principales
- **Resize Interactivo**: Arrastra las esquinas del recuadro de firma para ajustar su tamaño en tiempo real
- **Inputs Numéricos**: Control preciso con campos de entrada (ancho y alto en puntos PDF)
- **Aspect Ratio Lock**: Mantén la proporción de la firma activando un checkbox
- **Previsualización**: La firma se redimensiona visualmente en el PDF antes de firmar
- **Compatibilidad con Batch Signing**: Reutiliza la configuración de tamaño para múltiples documentos

#### Rangos de Tamaño
| Parámetro | Mínimo | Máximo | Unidad |
|-----------|--------|--------|--------|
| Ancho | 50 | 400 | puntos PDF |
| Alto | 30 | 200 | puntos PDF |

#### Casos de Uso
1. **Documentos con espacios variables**: Ajusta la firma a cualquier espacio disponible
2. **Firma corporativa consistente**: Define un tamaño estándar y reutiliza en lotes
3. **Control fino**: Inputs numéricos para precisión exacta

#### Mejoras de UX
- Handles visuales en las esquinas (aparecen al pasar el mouse)
- Indicador en tiempo real de dimensiones
- Validación de límites automática
- Interfaz responsive (funciona en mobile y desktop)

### 📖 Documentación Completa
- Guía de usuario en español
- Documentación técnica del backend
- Plan de pruebas detallado
- Instrucciones de integración
