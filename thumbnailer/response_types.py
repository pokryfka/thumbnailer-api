from typing import Dict, Optional
from pydantic import BaseModel, validator
from http import HTTPStatus
from json import dumps as json_dumps
from base64 import b64encode


class Response(BaseModel):
    statusCode: int
    headers: Dict[str, str] = []
    body: Optional[str] = ""
    isBase64Encoded: bool = False


class ResultResponse(Response):
    statusCode = HTTPStatus.OK.value


class ServerErrorResponse(Response):
    statusCode = HTTPStatus.INTERNAL_SERVER_ERROR


class BadRequestResponse(Response):
    statusCode = HTTPStatus.BAD_REQUEST.value


class NotFoundResponse(Response):
    statusCode = HTTPStatus.NOT_FOUND.value


class ForbiddenResponse(Response):
    statusCode = HTTPStatus.FORBIDDEN.value


class JSONResultResponse(ResultResponse):
    headers = {"Content-Type": "application/json"}
    body: str = ""

    @validator("body", pre=True, whole=True)
    def encode_body(cls, v):
        if isinstance(v, dict):
            try:
                return json_dumps(v)
            except ValueError:
                pass
        return v


class BinaryResultResponse(ResultResponse):
    def __init__(self, data, content_type):
        super().__init__()

        self.isBase64Encoded = True
        self.headers = {"content-type": content_type}
        self.body = b64encode(data).decode("utf-8")
