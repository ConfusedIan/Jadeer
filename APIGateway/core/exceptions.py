from fastapi import HTTPException

class ServiceUnavailableError(HTTPException):
    def __init__(self, detail: str = "Target service unavailable"):
        super().__init__(status_code=503, detail=detail)

class BadGatewayError(HTTPException):
    def __init__(self, detail: str = "Bad gateway"):
        super().__init__(status_code=502, detail=detail)

class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)
