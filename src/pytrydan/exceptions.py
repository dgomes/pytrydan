class TrydanError(Exception):
    """Base class for Trydan errors."""


class TrydanInvalidResponse(TrydanError):
    """Raised when Trydan returns an invalid response."""


class TrydanCommunicationError(TrydanError):
    """Raised when there is a communication error while talking to Trydan."""


class TrydanInvalidKeyword(TrydanError):
    """Raised when invalid keyword is used."""


class TrydanInvalidValue(TrydanError):
    """Raised when invalid value is used."""


class TrydanRetryLater(TrydanError):
    """Raised when value is not yet available."""
