import io
import os
import zipfile
import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from apps.users.models import APIToken
from .models import Document, SignatureProfile, SignatureBatch

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

class ESignatureAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='apitester', password='password123')
        self.token = APIToken.objects.create(user=self.user, name="Test Token")
        
        # Perfil de firma de prueba
        self.profile = SignatureProfile.objects.create(
            user=self.user,
            name="Certificados Escuela",
            description="Firma en página 1 abajo a la derecha",
            page=1,
            x=400,
            y=100,
            width=150,
            height=60
        )
        
        # Datos en memoria de archivos
        self.pdf_content = generate_empty_pdf()
        self.p12_content = generate_test_p12("testpass")
        
    def get_auth_header(self, token_str=None):
        if token_str is None:
            token_str = self.token.token
        return {'HTTP_AUTHORIZATION': f'Token {token_str}'}

    def test_unauthorized_requests(self):
        """Verifica que las peticiones sin token o con token inválido sean rechazadas."""
        url = reverse('api_profiles_list')
        
        # Caso 1: Sin header de autorización
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('Falta el encabezado', response.json()['error'])
        
        # Caso 2: Token inválido
        response = self.client.get(url, **self.get_auth_header("invalid_token_123"))
        self.assertEqual(response.status_code, 401)
        self.assertIn('inválido o inactivo', response.json()['error'])
        
        # Caso 3: Token inactivo
        self.token.is_active = False
        self.token.save()
        response = self.client.get(url, **self.get_auth_header())
        self.assertEqual(response.status_code, 401)

    def test_list_profiles(self):
        """Verifica el listado de perfiles de firma del usuario."""
        url = reverse('api_profiles_list')
        response = self.client.get(url, **self.get_auth_header())
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['profiles']), 1)
        self.assertEqual(data['profiles'][0]['name'], "Certificados Escuela")
        self.assertEqual(data['profiles'][0]['x'], 400.0)

    def test_sign_individual_coordinates_binary(self):
        """Firma individual enviando coordenadas manuales y solicitando el PDF binario directamente."""
        url = reverse('api_sign_individual')
        
        pdf_file = SimpleUploadedFile("original.pdf", self.pdf_content, content_type="application/pdf")
        p12_file = SimpleUploadedFile("firma.p12", self.p12_content, content_type="application/x-pkcs12")
        
        payload = {
            'password': 'testpass',
            'page': 1,
            'x': 100,
            'y': 200,
            'width': 200,
            'height': 50,
            'return_binary': 'true'
        }
        
        response = self.client.post(
            url,
            {**payload, 'pdf_file': pdf_file, 'p12_file': p12_file},
            format='multipart',
            **self.get_auth_header()
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        
        # Verificar trazabilidad en Base de Datos
        doc = Document.objects.filter(user=self.user, source='api').last()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.status, 'signed')
        self.assertEqual(doc.signature_x, 100.0)
        self.assertEqual(doc.signature_y, 200.0)
        
        # Limpieza de archivos del modelo de prueba
        if doc.original_file and os.path.exists(doc.original_file.path):
            os.remove(doc.original_file.path)
        if doc.signed_file and os.path.exists(doc.signed_file.path):
            os.remove(doc.signed_file.path)

    def test_sign_individual_profile_json(self):
        """Firma individual utilizando un SignatureProfile y solicitando respuesta JSON con link de descarga."""
        url = reverse('api_sign_individual')
        
        pdf_file = SimpleUploadedFile("test_doc.pdf", self.pdf_content, content_type="application/pdf")
        p12_file = SimpleUploadedFile("firma.p12", self.p12_content, content_type="application/x-pkcs12")
        
        payload = {
            'password': 'testpass',
            'profile_id': self.profile.id,
            'return_binary': 'false'
        }
        
        response = self.client.post(
            url,
            {**payload, 'pdf_file': pdf_file, 'p12_file': p12_file},
            format='multipart',
            **self.get_auth_header()
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('download_url', data['document'])
        
        # Verificar que coincida con el perfil
        doc = Document.objects.get(id=data['document']['id'])
        self.assertEqual(doc.signature_x, self.profile.x)
        self.assertEqual(doc.signature_width, self.profile.width)
        self.assertEqual(doc.source, 'api')
        
        # Probar la descarga segura del documento creado
        download_url = reverse('api_document_download', args=[doc.id])
        dl_response = self.client.get(download_url, **self.get_auth_header())
        self.assertEqual(dl_response.status_code, 200)
        self.assertEqual(dl_response['Content-Type'], 'application/pdf')
        
        # Limpieza
        if doc.original_file and os.path.exists(doc.original_file.path):
            os.remove(doc.original_file.path)
        if doc.signed_file and os.path.exists(doc.signed_file.path):
            os.remove(doc.signed_file.path)

    def test_sign_batch_binary(self):
        """Firma masiva enviando múltiples PDFs y retornando el ZIP binario."""
        url = reverse('api_sign_batch')
        
        doc1 = SimpleUploadedFile("cert1.pdf", self.pdf_content, content_type="application/pdf")
        doc2 = SimpleUploadedFile("cert2.pdf", self.pdf_content, content_type="application/pdf")
        p12_file = SimpleUploadedFile("firma.p12", self.p12_content, content_type="application/x-pkcs12")
        
        payload = {
            'password': 'testpass',
            'profile_id': self.profile.id,
            'return_binary': 'true'
        }
        
        # Enviamos 'documents' como lista en el diccionario de datos
        post_data = {
            'p12_file': p12_file,
            'password': payload['password'],
            'profile_id': payload['profile_id'],
            'return_binary': payload['return_binary'],
            'documents': [doc1, doc2]
        }
        
        response = self.client.post(
            url,
            post_data,
            **self.get_auth_header()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        
        # Verificar contenido del ZIP
        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes) as z:
            namelist = z.namelist()
            self.assertEqual(len(namelist), 2)
            self.assertIn("signed_cert1.pdf", namelist)
            self.assertIn("signed_cert2.pdf", namelist)
            
        # Verificar log en SignatureBatch
        batch_log = SignatureBatch.objects.filter(user=self.user, source='api').last()
        self.assertIsNotNone(batch_log)
        self.assertEqual(batch_log.document_count, 2)
        self.assertEqual(batch_log.signature_profile, self.profile)

    def test_sign_individual_invalid_password(self):
        """Verifica que al firmar con una contraseña incorrecta se retorne un error claro y amigable."""
        url = reverse('api_sign_individual')
        
        pdf_file = SimpleUploadedFile("original.pdf", self.pdf_content, content_type="application/pdf")
        p12_file = SimpleUploadedFile("firma.p12", self.p12_content, content_type="application/x-pkcs12")
        
        payload = {
            'password': 'wrongpassword',
            'page': 1,
            'x': 100,
            'y': 200,
            'width': 200,
            'height': 50,
            'return_binary': 'true'
        }
        
        response = self.client.post(
            url,
            {**payload, 'pdf_file': pdf_file, 'p12_file': p12_file},
            format='multipart',
            **self.get_auth_header()
        )
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('No se pudo cargar el certificado o la clave privada', data['error'])

