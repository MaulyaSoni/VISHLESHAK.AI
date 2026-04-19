"""
Custom exceptions for the backend
"""


class APIError(Exception):
    """Base API error"""
    status_code: int = 500
    message: str = "Internal server error"
    
    def __init__(self, message: str = None, status_code: int = None):
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error"""
    status_code = 400
    message = "Validation error"


class AuthenticationError(APIError):
    """Authentication error"""
    status_code = 401
    message = "Authentication required"


class AuthorizationError(APIError):
    """Authorization error"""
    status_code = 403
    message = "Access denied"


class NotFoundError(APIError):
    """Resource not found"""
    status_code = 404
    message = "Resource not found"
