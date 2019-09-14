from typing import Dict
from pydantic import BaseModel, ValidationError


class ApiEvent(BaseModel):
    resource: str
    headers: Dict[str, str]
    pathParameters: Dict[str, str]
