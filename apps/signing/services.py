import io
import os
import tempfile
from datetime import datetime, timezone

from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509.oid import NameOID

from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.layout import BoxConstraints
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata
from pyhanko.stamp.text import TextStampStyle

from .stamp import generate_signature_stamp


def _extract_cn_from_p12(p12_bytes: bytes, password: str) -> str:
    """Extrae el Common Name (CN) del certificado dentro del .p12."""
    try:
        private_key, certificate, _ = load_key_and_certificates(
            p12_bytes, password.encode('utf-8')
        )
        attrs = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if attrs:
            return attrs[0].value
    except Exception:
        pass
    return 'Firmante'


def sign_pdf_service(
    input_pdf_path: str,
    p12_content: bytes,
    password: str,
    page: int = 1,
    x: float = 50,
    y: float = 50,
    width: float = 250,
    height: float = 60,
) -> str:
    """
    Firma un PDF usando un certificado .p12.
    Genera una apariencia visual tipo FirmaEC: QR a la izquierda + texto a la derecha.
    Retorna la ruta del archivo PDF firmado temporal.
    """
    p12_temp_path = None
    stamp_img_path = None

    try:
        # ── 1. Guardar .p12 temporalmente ──────────────────────────────────
        with tempfile.NamedTemporaryFile(delete=False, suffix='.p12') as p12_tmp:
            p12_tmp.write(p12_content)
            p12_temp_path = p12_tmp.name

        # ── 2. Extraer nombre del firmante ─────────────────────────────────
        signer_name = _extract_cn_from_p12(p12_content, password)

        # ── 3. Cargar el firmante pyHanko ──────────────────────────────────
        signer = signers.SimpleSigner.load_pkcs12(
            p12_temp_path, passphrase=password.encode('utf-8')
        )

        # ── 4. Generar imagen de estampa (QR + texto) ──────────────────────
        now = datetime.now(tz=timezone.utc)
        stamp_png_bytes = generate_signature_stamp(
            signer_name=signer_name,
            document_path=input_pdf_path,
            timestamp=now,
            width_pt=width,
            height_pt=height,
        )

        # Guardar PNG temporal para pyHanko
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as img_tmp:
            img_tmp.write(stamp_png_bytes)
            stamp_img_path = img_tmp.name

        # ── 5. Construir el estilo de firma con la imagen como fondo ────────
        from PIL import Image as PILImage
        pil_img = PILImage.open(io.BytesIO(stamp_png_bytes))
        pdf_image = PdfImage(pil_img, box=BoxConstraints(width=width, height=height))

        # TextStampStyle con nuestra imagen PIL completa (QR + texto) como fondo.
        # stamp_text vacío porque todo el contenido ya está en la imagen.
        stamp_style = TextStampStyle(
            background=pdf_image,
            background_opacity=1.0,
            border_width=0,
            stamp_text='',
        )

        # ── 6. Firmar el PDF ────────────────────────────────────────────────
        output_pdf_path = tempfile.mktemp(suffix='.pdf')
        box_coords = (x, y, x + width, y + height)

        with open(input_pdf_path, 'rb') as doc:
            w = IncrementalPdfFileWriter(doc)
            append_signature_field(
                w,
                SigFieldSpec('FirmaDigital', box=box_coords, on_page=page - 1),
            )

            with open(output_pdf_path, 'wb') as out_f:
                pdf_signer = PdfSigner(
                    PdfSignatureMetadata(field_name='FirmaDigital'),
                    signer=signer,
                    stamp_style=stamp_style,
                )
                pdf_signer.sign_pdf(w, in_place=False, output=out_f)

        return output_pdf_path

    except Exception as e:
        raise Exception(f'Error en la firma digital: {str(e)}')

    finally:
        # Limpiar archivos temporales de credenciales
        for path in (p12_temp_path, stamp_img_path):
            if path and os.path.exists(path):
                os.remove(path)
