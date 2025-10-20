"""
Excepciones personalizadas de la aplicación
"""


class APIException(Exception):
    """Excepción base para todas las excepciones de la API"""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


# Excepciones de autenticación (401)
class UnauthorizedError(APIException):
    """Error cuando el usuario no está autenticado"""
    
    def __init__(self, message: str = "No autorizado"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


class InvalidCredentialsError(APIException):
    """Error cuando las credenciales son inválidas"""
    
    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(message, status_code=401, error_code="INVALID_CREDENTIALS")


class TokenExpiredError(APIException):
    """Error cuando el token JWT ha expirado"""
    
    def __init__(self, message: str = "Token expirado"):
        super().__init__(message, status_code=401, error_code="TOKEN_EXPIRED")


# Excepciones de autorización (403)
class ForbiddenError(APIException):
    """Error cuando el usuario no tiene permisos"""
    
    def __init__(self, message: str = "No tiene permisos para realizar esta acción"):
        super().__init__(message, status_code=403, error_code="FORBIDDEN")


# Excepciones de recursos no encontrados (404)
class NotFoundError(APIException):
    """Error cuando un recurso no existe"""
    
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class VideoNotFoundError(NotFoundError):
    """Error cuando un video no existe"""
    
    def __init__(self, video_id: str):
        super().__init__(f"Video con ID '{video_id}' no encontrado")
        self.error_code = "VIDEO_NOT_FOUND"


class UserNotFoundError(NotFoundError):
    """Error cuando un usuario no existe"""
    
    def __init__(self, user_id: str = None, email: str = None):
        if email:
            message = f"Usuario con email '{email}' no encontrado"
        elif user_id:
            message = f"Usuario con ID '{user_id}' no encontrado"
        else:
            message = "Usuario no encontrado"
        super().__init__(message)
        self.error_code = "USER_NOT_FOUND"


# Excepciones de validación (400)
class BadRequestError(APIException):
    """Error de solicitud incorrecta"""
    
    def __init__(self, message: str = "Solicitud incorrecta"):
        super().__init__(message, status_code=400, error_code="BAD_REQUEST")


class ValidationError(BadRequestError):
    """Error de validación de datos"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.error_code = "VALIDATION_ERROR"
        self.field = field


class DuplicateEmailError(BadRequestError):
    """Error cuando el email ya está registrado"""
    
    def __init__(self, email: str):
        super().__init__(f"El email '{email}' ya está registrado")
        self.error_code = "DUPLICATE_EMAIL"


class PasswordMismatchError(BadRequestError):
    """Error cuando las contraseñas no coinciden"""
    
    def __init__(self):
        super().__init__("Las contraseñas no coinciden")
        self.error_code = "PASSWORD_MISMATCH"


class InvalidFileTypeError(BadRequestError):
    """Error cuando el tipo de archivo no es válido"""
    
    def __init__(self, allowed_types: list[str]):
        types_str = ", ".join(allowed_types)
        super().__init__(f"Tipo de archivo no válido. Formatos permitidos: {types_str}")
        self.error_code = "INVALID_FILE_TYPE"


class FileSizeExceededError(BadRequestError):
    """Error cuando el archivo excede el tamaño máximo"""
    
    def __init__(self, max_size_mb: int):
        super().__init__(f"El archivo excede el tamaño máximo de {max_size_mb}MB")
        self.error_code = "FILE_SIZE_EXCEEDED"


class VideoDurationError(BadRequestError):
    """Error cuando la duración del video no es válida"""
    
    def __init__(self, min_seconds: int, max_seconds: int):
        super().__init__(
            f"La duración del video debe estar entre {min_seconds} y {max_seconds} segundos"
        )
        self.error_code = "INVALID_VIDEO_DURATION"


# Excepciones de conflicto (409)
class ConflictError(APIException):
    """Error de conflicto con el estado actual"""
    
    def __init__(self, message: str = "Conflicto con el estado actual del recurso"):
        super().__init__(message, status_code=409, error_code="CONFLICT")


class AlreadyVotedError(ConflictError):
    """Error cuando el usuario ya votó por un video"""
    
    def __init__(self):
        super().__init__("Ya ha votado por este video")
        self.error_code = "ALREADY_VOTED"


class VideoNotProcessedError(ConflictError):
    """Error cuando se intenta acceder a un video no procesado"""
    
    def __init__(self):
        super().__init__("El video aún no ha sido procesado")
        self.error_code = "VIDEO_NOT_PROCESSED"


class CannotDeleteVideoError(ConflictError):
    """Error cuando no se puede eliminar un video"""
    
    def __init__(self, reason: str = "El video no puede ser eliminado"):
        super().__init__(reason)
        self.error_code = "CANNOT_DELETE_VIDEO"


# Excepciones de servidor (500)
class InternalServerError(APIException):
    """Error interno del servidor"""
    
    def __init__(self, message: str = "Error interno del servidor"):
        super().__init__(message, status_code=500, error_code="INTERNAL_SERVER_ERROR")


class StorageError(InternalServerError):
    """Error al guardar o recuperar archivos"""
    
    def __init__(self, message: str = "Error al procesar el archivo"):
        super().__init__(message)
        self.error_code = "STORAGE_ERROR"


class ProcessingError(InternalServerError):
    """Error al procesar un video"""
    
    def __init__(self, message: str = "Error al procesar el video"):
        super().__init__(message)
        self.error_code = "PROCESSING_ERROR"
