from typing import Dict, Optional
from pydantic import BaseModel
from http import HTTPStatus


class Response(BaseModel):
    statusCode: int
    headers: Dict[str, str] = []
    body: Optional[str] = ""


class ResultResponse(Response):
    statusCode = HTTPStatus.OK.value


class ServerErrorResponse(Response):
    statusCode = HTTPStatus.INTERNAL_SERVER_ERROR


class BadRequestResponse(Response):
    statusCode = HTTPStatus.BAD_REQUEST.value


class ForbiddenResponse(Response):
    statusCode = HTTPStatus.FORBIDDEN.value
