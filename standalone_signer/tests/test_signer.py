import os
import sys
import unittest
import tempfile
import datetime
from unittest.mock import patch

# Asegurar que standalone_signer esté en el path para poder importar signer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from signer import PdfSigner
from signer.exceptions import (
    InvalidPasswordError,
    InvalidPdfError,
    InvalidCoordinatesError,
)

def generate_test_p12(password="testpass"):
    """Genera en memoria un certificado .p12 autofirmado válido para pruebas."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"EC"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Test Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"John Doe"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    ).sign(private_key, hashes.SHA256())
    
    p12_data = pkcs12.serialize_key_and_certificates(
        name=b"test-cert",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
    )
    return p12_data

def generate_empty_pdf():
    """Genera una estructura de PDF mínima y válida de 1 página."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources <<>> /Contents 4 0 R>> endobj\n"
        b"4 0 obj <</Length 0>> stream\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000056 00000 n \n"
        b"0000000111 00000 n \n"
        b"0000000212 00000 n \n"
        b"trailer <</Size 5 /Root 1 0 R>>\n"
        b"startxref\n"
        b"261\n"
        b"%%EOF\n"
    )

class TestPdfSigner(unittest.TestCase):
    def setUp(self):
        self.p12_content = generate_test_p12("testpass")
        self.pdf_content = generate_empty_pdf()
        
        self.temp_dir = tempfile.TemporaryDirectory()
        
        self.pdf_path = os.path.join(self.temp_dir.name, "input.pdf")
        with open(self.pdf_path, 'wb') as f:
            f.write(self.pdf_content)
            
        self.p12_path = os.path.join(self.temp_dir.name, "cert.p12")
        with open(self.p12_path, 'wb') as f:
            f.write(self.p12_content)
            
        self.output_path = os.path.join(self.temp_dir.name, "output.pdf")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_successful_signature_paths(self):
        """Prueba que el PDF se firme exitosamente usando rutas."""
        signer = PdfSigner()
        res = signer.sign(
            input_pdf=self.pdf_path,
            output_pdf=self.output_path,
            certificate=self.p12_path,
            password="testpass",
            page=1,
            x=100,
            y=100,
            width=200,
            height=50
        )
        self.assertEqual(res, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        self.assertGreater(os.path.getsize(self.output_path), len(self.pdf_content))

    def test_successful_signature_bytes(self):
        """Prueba que el PDF se firme exitosamente usando bytes."""
        signer = PdfSigner()
        res = signer.sign(
            input_pdf=self.pdf_content,
            output_pdf=self.output_path,
            certificate=self.p12_content,
            password="testpass",
            page=1,
            x=100,
            y=100,
            width=200,
            height=50
        )
        self.assertEqual(res, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        self.assertGreater(os.path.getsize(self.output_path), len(self.pdf_content))

    def test_invalid_password(self):
        """Prueba que se lance InvalidPasswordError al usar contraseña incorrecta."""
        signer = PdfSigner()
        with self.assertRaises(InvalidPasswordError):
            signer.sign(
                input_pdf=self.pdf_path,
                output_pdf=self.output_path,
                certificate=self.p12_path,
                password="wrongpassword"
            )

    def test_invalid_pdf_path(self):
        """Prueba que se lance InvalidPdfError si el PDF de entrada no existe."""
        signer = PdfSigner()
        with self.assertRaises(InvalidPdfError):
            signer.sign(
                input_pdf="non_existent.pdf",
                output_pdf=self.output_path,
                certificate=self.p12_path,
                password="testpass"
            )

    def test_invalid_page(self):
        """Prueba que se lance InvalidPdfError si la página está fuera de rango."""
        signer = PdfSigner()
        with self.assertRaises(InvalidPdfError):
            signer.sign(
                input_pdf=self.pdf_path,
                output_pdf=self.output_path,
                certificate=self.p12_path,
                password="testpass",
                page=2 # El PDF solo tiene 1 página
            )

    def test_invalid_coordinates(self):
        """Prueba que se lance InvalidCoordinatesError si las coordenadas son negativas."""
        signer = PdfSigner()
        with self.assertRaises(InvalidCoordinatesError):
            signer.sign(
                input_pdf=self.pdf_path,
                output_pdf=self.output_path,
                certificate=self.p12_path,
                password="testpass",
                x=-10
            )

    @patch('pyhanko.sign.timestamps.HTTPTimeStamper')
    def test_signature_with_tsa_url(self, mock_tsa):
        """Prueba que el firmador acepte y configure el sellado de tiempo."""
        from pyhanko.sign.timestamps import DummyTimeStamper
        from asn1crypto import x509 as asn1_x509, keys as asn1_keys
        
        # Generar certificados TSA dummy
        tsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        tsa_subject = tsa_issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"EC"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Test TSA"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"Test TSA"),
        ])
        tsa_cert = x509.CertificateBuilder().subject_name(
            tsa_subject
        ).issuer_name(
            tsa_issuer
        ).public_key(
            tsa_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
        ).sign(tsa_key, hashes.SHA256())

        asn1_cert_obj = asn1_x509.Certificate.load(tsa_cert.public_bytes(serialization.Encoding.DER))
        asn1_key_obj = asn1_keys.PrivateKeyInfo.load(
            tsa_key.private_bytes(
                serialization.Encoding.DER,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            )
        )
        mock_tsa.return_value = DummyTimeStamper(tsa_cert=asn1_cert_obj, tsa_key=asn1_key_obj)

        signer = PdfSigner()
        res = signer.sign(
            input_pdf=self.pdf_path,
            output_pdf=self.output_path,
            certificate=self.p12_path,
            password="testpass",
            page=1,
            x=100,
            y=100,
            width=200,
            height=50,
            tsa_url="https://tsa.example.com",
            tsa_username="cliuser",
            tsa_password="clipassword"
        )
        self.assertEqual(res, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        mock_tsa.assert_called_once_with(url="https://tsa.example.com", auth=("cliuser", "clipassword"))

    def test_signature_no_extension_file(self):
        """Prueba que se procese un certificado sin extensión de archivo (flujo de bytes o binario puro)."""
        no_ext_cert_path = os.path.join(self.temp_dir.name, "cert_raw_bin_no_ext")
        with open(no_ext_cert_path, 'wb') as f:
            f.write(self.p12_content)

        signer = PdfSigner()
        res = signer.sign(
            input_pdf=self.pdf_path,
            output_pdf=self.output_path,
            certificate=no_ext_cert_path,
            password="testpass",
            page=1,
            x=100,
            y=100,
            width=200,
            height=50
        )
        self.assertEqual(res, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))

    @patch('pyhanko.sign.signers.SimpleSigner.load_pkcs12_data', side_effect=ValueError("Formato no soportado por pyHanko directo"))
    def test_signature_fallback_manual_extraction(self, mock_load_pkcs12_data):
        """Prueba que el fallback manual con cryptography extraiga private_key, cert e instancie SimpleSigner cuando pyHanko directo falla (Security Data/legacy)."""
        signer = PdfSigner()
        res = signer.sign(
            input_pdf=self.pdf_path,
            output_pdf=self.output_path,
            certificate=self.p12_content,
            password="testpass",
            page=1,
            x=100,
            y=100,
            width=200,
            height=50
        )
        self.assertEqual(res, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        mock_load_pkcs12_data.assert_called_once()

if __name__ == '__main__':
    unittest.main()
