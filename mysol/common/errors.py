from fastapi import HTTPException

class MysolHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)

class InvalidFieldFormatError(MysolHTTPException):
    def __init__(self, message: str = "Invalid field format") -> None:
        super().__init__(status_code=400, detail=message)