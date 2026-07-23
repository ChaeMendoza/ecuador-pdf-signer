import sys
import argparse
from signer import PdfSigner
from signer.exceptions import SignerError

def main():
    parser = argparse.ArgumentParser(
        description="Firma electrónica independiente de PDFs con certificados PKCS#12 al estilo FirmaEC."
    )
    parser.add_argument(
        "--input", required=True, help="Ruta del archivo PDF de entrada."
    )
    parser.add_argument(
        "--output", required=True, help="Ruta del archivo PDF firmado de salida."
    )
    parser.add_argument(
        "--certificate", required=True, help="Ruta del certificado PKCS#12 (.p12 o .pfx)."
    )
    parser.add_argument(
        "--password", required=True, help="Contraseña del certificado."
    )
    parser.add_argument(
        "--page", type=int, default=1, help="Número de página para aplicar la firma (1-indexed). Defecto: 1."
    )
    parser.add_argument(
        "--x", type=float, default=50.0, help="Coordenada X (en puntos) de la firma. Defecto: 50."
    )
    parser.add_argument(
        "--y", type=float, default=50.0, help="Coordenada Y (en puntos) de la firma. Defecto: 50."
    )
    parser.add_argument(
        "--width", type=float, default=250.0, help="Ancho de la estampa (en puntos). Defecto: 250."
    )
    parser.add_argument(
        "--height", type=float, default=60.0, help="Alto de la estampa (en puntos). Defecto: 60."
    )
    parser.add_argument(
        "--tsa-url", default=None, help="URL de la Autoridad de Sellado de Tiempo (TSA) compatible con RFC 3161."
    )
    parser.add_argument(
        "--tsa-user", default=None, help="Nombre de usuario para autenticación con el servidor TSA."
    )
    parser.add_argument(
        "--tsa-pass", default=None, help="Contraseña para autenticación con el servidor TSA."
    )

    args = parser.parse_args()

    signer = PdfSigner()
    try:
        signer.sign(
            input_pdf=args.input,
            output_pdf=args.output,
            certificate=args.certificate,
            password=args.password,
            page=args.page,
            x=args.x,
            y=args.y,
            width=args.width,
            height=args.height,
            tsa_url=args.tsa_url,
            tsa_username=args.tsa_user,
            tsa_password=args.tsa_pass,
        )
        print(f"Éxito: PDF firmado correctamente en '{args.output}'")
        sys.exit(0)
    except SignerError as e:
        sys.stderr.write(f"Error de firma: {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error inesperado: {str(e)}\n")
        sys.exit(2)

if __name__ == "__main__":
    main()
