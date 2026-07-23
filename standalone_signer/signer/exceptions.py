class SignerError(Exception):
    """Base exception for standalone_signer package."""
    pass


class InvalidCertificateError(SignerError):
    """Raised when the certificate format is invalid or corrupted."""
    pass


class InvalidPasswordError(SignerError):
    """Raised when the certificate password is incorrect."""
    pass


class InvalidPdfError(SignerError):
    """Raised when the input PDF is invalid or cannot be processed."""
    pass


class InvalidCoordinatesError(SignerError):
    """Raised when the signature coordinates or dimensions are invalid."""
    pass
