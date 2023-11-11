from enum import Enum


class SwaggerTags(str, Enum):
    CARD = 'Card'
    TRANSACTION = 'Transaction'


class BaseSwaggerAPIViewDoc:
    tags = []
    summary = ...
    description = ...
    responses = None
