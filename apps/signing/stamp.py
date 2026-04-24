"""
Genera una imagen compuesta (QR + texto) que simula la firma visible
estilo FirmaEC: QR a la izquierda y texto a la derecha.
"""
import io
import hashlib
from datetime import datetime

import qrcode
from PIL import Image, ImageDraw, ImageFont


# Rutas de fuentes disponibles en el contenedor Debian
_FONTS = {
    'mono': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
    ],
    'bold': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ],
    'regular': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ],
}


def _load_font(style: str, size: int) -> ImageFont.FreeTypeFont:
    for path in _FONTS.get(style, []):
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _build_qr_image(qr_text: str, target_size: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
    img = img.resize((target_size, target_size), Image.LANCZOS)
    return img


def generate_signature_stamp(
    signer_name: str,
    document_path: str,
    timestamp: datetime,
    width_pt: float = 250,
    height_pt: float = 60,
    dpi: int = 150,
) -> bytes:
    """
    Genera la imagen de la firma visible al estilo FirmaEC.

    Retorna los bytes PNG de la imagen.

    :param signer_name:    Nombre completo del firmante (del CN del certificado).
    :param document_path:  Ruta al PDF original (para calcular hash).
    :param timestamp:      Fecha/hora de la firma.
    :param width_pt:       Ancho del bloque de firma en puntos PDF.
    :param height_pt:      Alto del bloque de firma en puntos PDF.
    :param dpi:            Resolución en pixeles por pulgada para la imagen.
    """
    # 1 punto = 1/72 pulgada → convertir a píxeles
    px_per_pt = dpi / 72.0
    w_px = int(width_pt * px_per_pt)
    h_px = int(height_pt * px_per_pt)

    # Calcular hash del documento (primeros 32 hex)
    doc_hash = ''
    try:
        sha = hashlib.sha256()
        with open(document_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha.update(chunk)
        doc_hash = sha.hexdigest()
    except Exception:
        doc_hash = 'N/A'

    # Contenido del QR
    ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    qr_text = (
        f"Firmado por: {signer_name}\n"
        f"Fecha: {ts_str}\n"
        f"Documento: {doc_hash}\n"
        f"Valide en: https://www.firmaec.gob.ec"
    )

    # Tamaño del QR (ocupa el alto completo con pequeño margen)
    qr_size = h_px - 4

    # Crear lienzo
    canvas = Image.new('RGB', (w_px, h_px), 'white')
    draw = ImageDraw.Draw(canvas)

    # Pegar QR
    qr_img = _build_qr_image(qr_text, qr_size)
    canvas.paste(qr_img, (2, 2))

    # Área de texto
    text_x = qr_size + 8
    available_w = w_px - text_x - 4

    # Fuentes
    size_small = max(7, int(h_px * 0.13))
    size_name  = max(9, int(h_px * 0.19))
    font_mono  = _load_font('mono', size_small)
    font_bold  = _load_font('bold', size_name)

    # Líneas de texto fijo
    line1 = 'Validar en: SignApp o FirmaEC.'
    line2 = 'Firmado electrónicamente por:'

    y = int(h_px * 0.05)
    draw.text((text_x, y), line1, fill='#333333', font=font_mono)
    y += size_small + int(h_px * 0.06)
    draw.text((text_x, y), line2, fill='#333333', font=font_mono)

    # Nombre en mayúsculas y negrita — dividir en dos líneas si es largo
    name_upper = signer_name.upper()
    words = name_upper.split()
    mid = len(words) // 2 if len(words) > 2 else len(words)
    name_line1 = ' '.join(words[:mid])
    name_line2 = ' '.join(words[mid:]) if words[mid:] else ''

    y += size_small + int(h_px * 0.10)
    draw.text((text_x, y), name_line1, fill='black', font=font_bold)
    if name_line2:
        y += size_name + int(h_px * 0.04)
        draw.text((text_x, y), name_line2, fill='black', font=font_bold)

    # Serializar como PNG
    buf = io.BytesIO()
    canvas.save(buf, format='PNG', dpi=(dpi, dpi))
    return buf.getvalue()
