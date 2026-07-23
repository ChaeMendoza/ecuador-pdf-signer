from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509.oid import NameOID
from pyhanko.sign import signers
from pyhanko.sign.signers.pdf_cms import (
    translate_pyca_cryptography_key_to_asn1,
    translate_pyca_cryptography_cert_to_asn1,
)
from pyhanko_certvalidator.registry import SimpleCertificateStore
from .exceptions import InvalidCertificateError, InvalidPasswordError

def extract_cn_from_p12(p12_bytes: bytes, password: str) -> str:
    """
    Extrae el Common Name (CN) del certificado dentro de los bytes del PKCS#12.
    Lanza excepciones específicas en caso de fallos.
    """
    try:
        pass_bytes = password.encode('utf-8') if isinstance(password, str) and password is not None else password
        private_key, certificate, _ = load_key_and_certificates(
            p12_bytes, pass_bytes
        )
    except ValueError as e:
        err_msg = str(e)
        if any(keyword in err_msg.lower() for keyword in ["decryption failed", "mac verification failed", "password"]):
            raise InvalidPasswordError("La contraseña del certificado es incorrecta.") from e
        else:
            raise InvalidCertificateError("El archivo de certificado no es un PKCS#12 válido o está corrupto.") from e
    except Exception as e:
        raise InvalidCertificateError(f"Error al leer el certificado: {str(e)}") from e

    if not certificate:
        raise InvalidCertificateError("El archivo PKCS#12 no contiene un certificado principal.")

    attrs = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    if attrs:
        return attrs[0].value
    return 'Firmante'


def load_signer_from_pkcs12_bytes(p12_bytes: bytes, password: str) -> signers.SimpleSigner:
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
    except ValueError as e:
        err_msg = str(e)
        if any(keyword in err_msg.lower() for keyword in ["decryption failed", "mac verification failed", "password"]):
            raise InvalidPasswordError("La contraseña del certificado es incorrecta.") from e
        else:
            raise InvalidCertificateError("El archivo de certificado no es un PKCS#12 válido o está corrupto.") from e
    except Exception as e:
        raise InvalidCertificateError(f"Error al leer el certificado: {str(e)}") from e

    if not private_key or not certificate:
        raise InvalidCertificateError("El archivo PKCS#12 no contiene una clave privada o certificado principal válido.")

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

