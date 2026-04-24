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

## 🤝 Contribuciones

Si deseas mejorar el proyecto, siéntete libre de hacer un _fork_ y abrir un _Pull Request_. Todas las contribuciones son bienvenidas.
