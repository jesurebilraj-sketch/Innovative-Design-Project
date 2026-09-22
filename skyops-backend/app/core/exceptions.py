"""Application-specific exceptions for SkyOps backend."""

class SkyOpsException(Exception):
    """Base exception for all SkyOps errors."""
    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundException(SkyOpsException):
    """Raised when an entity is not found."""
    def __init__(self, message: str = "Entity not found", error_code: str = "NOT_FOUND"):
        super().__init__(message=message, status_code=404, error_code=error_code)


class FlightNotFoundError(NotFoundException):
    """Raised when a specific flight cannot be found."""
    def __init__(self, flight_id: str):
        super().__init__(message=f"Flight with ID '{flight_id}' not found", error_code="FLIGHT_NOT_FOUND")


class GateNotFoundError(NotFoundException):
    """Raised when a specific gate cannot be found."""
    def __init__(self, gate_id: str):
        super().__init__(message=f"Gate with ID '{gate_id}' not found", error_code="GATE_NOT_FOUND")


class AirportNotFoundError(NotFoundException):
    """Raised when a specific airport cannot be found."""
    def __init__(self, airport_id: str):
        super().__init__(message=f"Airport with ID '{airport_id}' not found", error_code="AIRPORT_NOT_FOUND")


class GateConflictException(SkyOpsException):
    """Raised when an operational conflict occurs on gate assignment."""
    def __init__(self, message: str = "Conflict detected for the requested gate assignment"):
        super().__init__(message=message, status_code=409, error_code="GATE_CONFLICT")


class NoFeasibleGateError(SkyOpsException):
    """Raised when no compatible, conflict-free gate can be found."""
    def __init__(self, message: str = "No feasible gate available satisfying operational constraints"):
        super().__init__(message=message, status_code=422, error_code="NO_FEASIBLE_GATE")


class ExternalServiceException(SkyOpsException):
    """Raised when third-party integration fails."""
    def __init__(self, message: str = "External service failed", status_code: int = 502, error_code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(message=message, status_code=status_code, error_code=error_code)


class WeatherProviderError(ExternalServiceException):
    """Raised when the weather provider fails or times out."""
    def __init__(self, message: str = "Failed to retrieve weather data from provider"):
        super().__init__(message=message, status_code=502, error_code="WEATHER_PROVIDER_ERROR")


class PredictorUnavailableError(ExternalServiceException):
    """Raised when the delay prediction service is unreachable or fails."""
    def __init__(self, message: str = "Predictor service unavailable"):
        super().__init__(message=message, status_code=503, error_code="PREDICTOR_UNAVAILABLE")


class InvalidPredictionError(SkyOpsException):
    """Raised when a predictor output fails validation."""
    def __init__(self, message: str = "Invalid prediction response from model"):
        super().__init__(message=message, status_code=422, error_code="INVALID_PREDICTION")


class UnauthorizedOperatorError(SkyOpsException):
    """Raised when an action requires operator privileges."""
    def __init__(self, message: str = "Operator role required to perform this action"):
        super().__init__(message=message, status_code=403, error_code="OPERATOR_REQUIRED")


class AuthenticationError(SkyOpsException):
    """Raised when an authentication token is invalid or missing."""
    def __init__(self, message: str = "Invalid or missing authentication credentials"):
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED")
