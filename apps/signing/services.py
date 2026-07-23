import io
import os
import tempfile
from datetime import datetime, timezone

from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509.oid import NameOID

from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import signers
from pyhanko.stamp import TextStampStyle
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.layout import BoxConstraints
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import append_signature_field, SigFieldSpec
from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata

from .stamp import generate_signature_stamp


def get_pdf_page_size(pdf_path: str, page: int = 1) -> tuple:
    """Obtiene el ancho y alto de una página PDF en puntos."""
    with open(pdf_path, 'rb') as f:
        reader = PdfFileReader(f, strict=False)
        page_ref, _ = reader.find_page_for_modification(page - 1)
        page_obj = page_ref.get_object()
        box = page_obj['/MediaBox']
        width = float(box[2] - box[0])
        height = float(box[3] - box[1])
        return width, height


def _extract_cn_from_p12(p12_bytes: bytes, password: str) -> str:
    """Extrae el Common Name (CN) del certificado dentro del .p12."""
    try:
        pass_bytes = password.encode('utf-8') if isinstance(password, str) and password is not None else password
        private_key, certificate, _ = load_key_and_certificates(
            p12_bytes, pass_bytes
        )
        attrs = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if attrs:
            return attrs[0].value
    except Exception:
        pass
    return 'Firmante'


def _load_signer_from_p12_bytes(p12_bytes: bytes, password: str) -> signers.SimpleSigner:
    """
    Carga un SimpleSigner de pyHanko a partir de bytes de un archivo PKCS#12 (.p12/.pfx u otros sin extensión).
    Altamente tolerante a fallos y compatible con certificados legacy (ej. Security Data) y estándar (ej. Uanataca).

    1. Intenta cargar directamente los bytes usando pyHanko `SimpleSigner.load_pkcs12_data`.
    2. Si pyHanko falla, ejecuta la extracción manual usando `cryptography` e instancia `SimpleSigner`
       con la llave privada, certificado principal y certificados adicionales.
    """
    pass_bytes = password.encode('utf-8') if isinstance(password, str) and password is not None else password

    # 1. Intento principal usando pyHanko en memoria
    try:
        signer = signers.SimpleSigner.load_pkcs12_data(p12_bytes, passphrase=pass_bytes)
        if signer is not None:
            return signer
    except Exception:
        pass

    # 2. Fallback de extracción manual con cryptography (para Security Data o formatos legacy/crudos)
    try:
        private_key, certificate, additional_certificates = load_key_and_certificates(
            p12_bytes, pass_bytes
        )
    except Exception as e:
        raise ValueError(
            "No se pudo cargar el certificado o la clave privada. "
            "Verifique que la contraseña sea correcta y que el archivo de firma sea válido."
        ) from e

    if not private_key or not certificate:
        raise ValueError(
            "No se pudo cargar el certificado o la clave privada. "
            "Verifique que la contraseña sea correcta y que el archivo esté en formato PKCS#12 válido."
        )

    from pyhanko.sign.signers.pdf_cms import (
        translate_pyca_cryptography_key_to_asn1,
        translate_pyca_cryptography_cert_to_asn1,
    )
    from pyhanko_certvalidator.registry import SimpleCertificateStore

    kinfo = translate_pyca_cryptography_key_to_asn1(private_key)
    cert_asn1 = translate_pyca_cryptography_cert_to_asn1(certificate)

    cs = SimpleCertificateStore()
    if additional_certificates:
        other_certs_asn1 = [
            translate_pyca_cryptography_cert_to_asn1(c)
            for c in additional_certificates
            if c is not None
        ]
        cs.register_multiple(other_certs_asn1)

    return signers.SimpleSigner(
        signing_key=kinfo,
        signing_cert=cert_asn1,
        cert_registry=cs,
    )


def sign_pdf_service(
    input_pdf_path: str,
    p12_content: bytes,
    password: str,
    page: int = 1,
    x: float = 50,
    y: float = 50,
    width: float = 250,
    height: float = 60,
    tsa_url: str = None,
    tsa_username: str = None,
    tsa_password: str = None,
) -> str:
    """
    Firma un PDF usando un certificado .p12.
    Genera una apariencia visual tipo FirmaEC: QR a la izquierda + texto a la derecha.
    Retorna la ruta del archivo PDF firmado temporal.
    """
    stamp_img_path = None

    try:
        # ── 1. Extraer nombre del firmante ─────────────────────────────────
        signer_name = _extract_cn_from_p12(p12_content, password)

        # ── 2. Cargar el firmante pyHanko (en memoria, soporta Uanataca y Security Data) ──
        signer = _load_signer_from_p12_bytes(p12_content, password)

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
            w = IncrementalPdfFileWriter(doc, strict=False)
            append_signature_field(
                w,
                SigFieldSpec('FirmaDigital', box=box_coords, on_page=page - 1),
            )

            # Configurar sellado de tiempo si se especifica tsa_url
            timestamper = None
            if tsa_url:
                from pyhanko.sign.timestamps import HTTPTimeStamper
                tsa_auth = None
                if tsa_username and tsa_password:
                    tsa_auth = (tsa_username, tsa_password)
                timestamper = HTTPTimeStamper(url=tsa_url, auth=tsa_auth)

            with open(output_pdf_path, 'wb') as out_f:
                pdf_signer = PdfSigner(
                    PdfSignatureMetadata(field_name='FirmaDigital'),
                    signer=signer,
                    stamp_style=stamp_style,
                    timestamper=timestamper,
                )
                pdf_signer.sign_pdf(w, in_place=False, output=out_f)

        return output_pdf_path

    except Exception as e:
        raise Exception(f'Error en la firma digital: {str(e)}')

    finally:
        # Limpiar archivos temporales
        if stamp_img_path and os.path.exists(stamp_img_path):
            os.remove(stamp_img_path)
