from pyhanko.pdf_utils.reader import PdfFileReader
from .exceptions import InvalidPdfError

def get_pdf_page_count(pdf_path: str) -> int:
    """Obtiene el número total de páginas del PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfFileReader(f, strict=False)
            return int(reader.root['/Pages']['/Count'])
    except Exception as e:
        raise InvalidPdfError(f"No se pudo leer el archivo PDF: {str(e)}") from e


def get_pdf_page_size(pdf_path: str, page: int = 1) -> tuple:
    """Obtiene el ancho y alto de una página PDF en puntos."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfFileReader(f, strict=False)
            total_pages = int(reader.root['/Pages']['/Count'])
            if page < 1 or page > total_pages:
                raise InvalidPdfError(f"Página {page} fuera de rango (total páginas: {total_pages}).")
            
            page_ref, _ = reader.find_page_for_modification(page - 1)
            page_obj = page_ref.get_object()
            box = page_obj['/MediaBox']
            width = float(box[2] - box[0])
            height = float(box[3] - box[1])
            return width, height
    except InvalidPdfError:
        raise
    except Exception as e:
        raise InvalidPdfError(f"Error al obtener tamaño de página del PDF: {str(e)}") from e
