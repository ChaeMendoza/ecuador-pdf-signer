import os
import tempfile
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata
from pyhanko.stamp import text

def sign_pdf_service(input_pdf_path, p12_content, password, page=1, x=50, y=50, width=200, height=50):
    """
    Firma un PDF usando un certificado .p12.
    Retorna la ruta del archivo PDF firmado temporal.
    """
    p12_temp_path = None
    try:
        # Guardar temporalmente el contenido del p12 en un archivo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".p12") as p12_temp:
            p12_temp.write(p12_content)
            p12_temp_path = p12_temp.name
            
        signer = signers.SimpleSigner.load_pkcs12(p12_temp_path, passphrase=password.encode('utf-8'))
        
        output_pdf_path = tempfile.mktemp(suffix=".pdf")
        
        with open(input_pdf_path, 'rb') as doc:
            w = IncrementalPdfFileWriter(doc)
            # Asignamos una posición visible en la página (x1, y1, x2, y2) y en la página correcta (0-indexed)
            box_coords = (x, y, x + width, y + height)
            append_signature_field(w, SigFieldSpec('FirmaDigital', box=box_coords, on_page=page - 1))
            
            # Configuramos un estilo de estampa visible
            stamp_style = text.TextStampStyle(
                stamp_text='Firmado digitalmente por: %(signer)s\nFecha: %(ts)s'
            )
            
            with open(output_pdf_path, 'wb') as out_f:
                pdf_signer = PdfSigner(
                    PdfSignatureMetadata(field_name='FirmaDigital'), signer=signer, stamp_style=stamp_style
                )
                pdf_signer.sign_pdf(w, in_place=False, bytes_reserved=8192, output=out_f)
                
        return output_pdf_path
    except Exception as e:
        raise Exception(f"Error en la firma digital: {str(e)}")
    finally:
        # Limpiar el certificado temporal del sistema de archivos
        if p12_temp_path and os.path.exists(p12_temp_path):
            os.remove(p12_temp_path)
