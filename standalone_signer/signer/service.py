import io
import os
import tempfile
from datetime import datetime, timezone
from PIL import Image as PILImage

from pyhanko.sign import signers
from pyhanko.stamp import TextStampStyle
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.layout import BoxConstraints
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import append_signature_field, SigFieldSpec
from pyhanko.sign.signers.pdf_signer import PdfSigner as PyHankoPdfSigner, PdfSignatureMetadata

from .certificate import extract_cn_from_p12, load_signer_from_pkcs12_bytes
from .pdf import get_pdf_page_count
from .validation import validate_coordinates, validate_page, validate_files
from .exceptions import SignerError, InvalidCertificateError, InvalidPdfError

class PdfSigner:
    """
    Clase principal para realizar firmas electrónicas visibles en PDFs
    al estilo FirmaEC, compatible con certificados PKCS#12 (.p12/.pfx).
    """

    def sign(
        self,
        input_pdf,
        output_pdf: str,
        certificate,
        password: str,
        page: int = 1,
        x: float = 50,
        y: float = 50,
        width: float = 250,
        height: float = 60,
        tsa_url: str = None,
        tsa_username: str = None,
        tsa_password: str = None,
        **kwargs
    ) -> str:
        """
        Firma un archivo PDF utilizando un certificado PKCS#12 (.p12/.pfx).

        :param input_pdf: Ruta al PDF original (str) o bytes con el contenido.
        :param output_pdf: Ruta de destino para guardar el PDF firmado (str).
        :param certificate: Ruta al certificado .p12 (str) o bytes con su contenido.
        :param password: Contraseña para desencriptar el certificado (str).
        :param page: Página donde ubicar la estampa visual (1-indexed).
        :param x: Coordenada X (puntos PDF).
        :param y: Coordenada Y (puntos PDF).
        :param width: Ancho de la estampa (puntos PDF).
        :param height: Alto de la estampa (puntos PDF).
        :return: Ruta absoluta del archivo PDF firmado (str).
        """
        temp_files_to_cleanup = []

        try:
            # 1. Validar y resolver PDF de entrada
            if isinstance(input_pdf, bytes):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(input_pdf)
                    input_pdf_path = tmp.name
                temp_files_to_cleanup.append(input_pdf_path)
            elif isinstance(input_pdf, str):
                input_pdf_path = input_pdf
                validate_files(input_pdf_path)
            else:
                raise InvalidPdfError("El parámetro input_pdf debe ser una ruta de archivo (str) o bytes.")

            # 2. Validar y resolver Certificado
            if isinstance(certificate, bytes):
                p12_bytes = certificate
            elif isinstance(certificate, str):
                validate_files(input_pdf_path, certificate_path=certificate)
                try:
                    with open(certificate, 'rb') as f:
                        p12_bytes = f.read()
                except Exception as e:
                    raise InvalidCertificateError(f"No se pudo leer el archivo de certificado: {str(e)}") from e
            else:
                raise InvalidCertificateError("El parámetro certificate debe ser una ruta de archivo (str) o bytes.")

            # 3. Validar parámetros de maquetación y coordenadas
            validate_coordinates(x, y, width, height)

            # 4. Validar página solicitada
            total_pages = get_pdf_page_count(input_pdf_path)
            validate_page(page, total_pages)

            # 5. Validar contraseña y extraer Common Name (CN)
            signer_name = extract_cn_from_p12(p12_bytes, password)

            # 6. Cargar el firmante de pyHanko (en memoria, sin asumir extensión y con soporte legacy)
            signer = load_signer_from_pkcs12_bytes(p12_bytes, password)

            # 8. Generar imagen de la firma (QR + texto descriptivo)
            from .utils import generate_signature_stamp
            now = datetime.now(tz=timezone.utc)
            stamp_png_bytes = generate_signature_stamp(
                signer_name=signer_name,
                document_path=input_pdf_path,
                timestamp=now,
                width_pt=width,
                height_pt=height,
            )

            # 9. Inicializar objeto de imagen y estilo en pyHanko
            pil_img = PILImage.open(io.BytesIO(stamp_png_bytes))
            pdf_image = PdfImage(pil_img, box=BoxConstraints(width=width, height=height))
            stamp_style = TextStampStyle(
                background=pdf_image,
                background_opacity=1.0,
                border_width=0,
                stamp_text='',
            )

            # 10. Aplicar la firma al PDF original incrementalmente
            box_coords = (x, y, x + width, y + height)
            output_dir = os.path.dirname(output_pdf)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            try:
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

                    with open(output_pdf, 'wb') as out_f:
                        pdf_signer = PyHankoPdfSigner(
                            PdfSignatureMetadata(field_name='FirmaDigital'),
                            signer=signer,
                            stamp_style=stamp_style,
                            timestamper=timestamper,
                        )
                        pdf_signer.sign_pdf(w, in_place=False, output=out_f)
            except Exception as e:
                raise SignerError(f"Fallo al escribir el PDF firmado incremental: {str(e)}") from e

            return output_pdf

        finally:
            # Eliminar todos los archivos temporales creados
            for path in temp_files_to_cleanup:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
