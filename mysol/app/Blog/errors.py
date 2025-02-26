from mysol.common.errors import MysolHTTPException

class BlognameAlreadyExistsError(MysolHTTPException):
    def __init__(self, message: str = "이미 존재하는 블로그 이름입니다.") -> None:
        super().__init__(status_code=400, detail=message)

class BlogNotFoundError(MysolHTTPException):
    def __init__(self, message: str = "해당 블로그를 찾을 수 없습니다.") -> None:
        super().__init__(status_code=404, detail=message)

class InvalidFieldFormatError(MysolHTTPException):
    def __init__(self, message: str = "형식이 올바르지 않습니다.") -> None:
        super().__init__(status_code=400, detail=message)

class MissingRequiredFieldError(MysolHTTPException):
    def __init__(self, message: str = "빠진 항목이 존재합니다.") -> None:
        super().__init__(status_code=400, detail=message)

class UserUnsignedError(MysolHTTPException):
    def __init__(self, message: str = "로그인되지 않았습니다.") -> None:
        super().__init__(status_code=401, detail=message)

class BlogAlreadyExistsError(MysolHTTPException):
    def __init__(self, message: str="이미 블로그가 존재하는 유저입니다.") -> None:
        super().__init__(status_code=400, detail=message)