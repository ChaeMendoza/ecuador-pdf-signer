import os
from .exceptions import InvalidCoordinatesError, InvalidPdfError

def validate_files(input_pdf_path: str, certificate_path: str = None):
    """Verifica que los archivos existan en el sistema."""
    if not os.path.exists(input_pdf_path):
        raise InvalidPdfError(f"El archivo PDF de entrada no existe: {input_pdf_path}")
    if certificate_path and not os.path.exists(certificate_path):
        raise InvalidPdfError(f"El archivo de certificado no existe: {certificate_path}")


def validate_coordinates(x, y, width, height):
    """Valida que los valores de las coordenadas sean válidos."""
    try:
        x = float(x)
        y = float(y)
        width = float(width)
        height = float(height)
    except (ValueError, TypeError) as e:
        raise InvalidCoordinatesError("Las coordenadas (x, y, width, height) deben ser números.") from e
        
    if x < 0 or y < 0:
        raise InvalidCoordinatesError("Las coordenadas x e y deben ser números no negativos.")
    if width <= 0 or height <= 0:
        raise InvalidCoordinatesError("El ancho y alto deben ser mayores que cero.")


def validate_page(page, total_pages):
    """Valida que el número de página solicitado sea correcto."""
    try:
        page = int(page)
    except (ValueError, TypeError) as e:
        raise InvalidPdfError("El número de página debe ser un número entero.") from e
        
    if page < 1:
        raise InvalidPdfError("El número de página debe ser 1 o mayor.")
    if total_pages is not None and page > total_pages:
        raise InvalidPdfError(f"El número de página ({page}) excede las páginas totales del PDF ({total_pages}).")
