"""Shared constants."""

HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "INTERNAL_ERROR": 500,
}

ERROR_MESSAGES = {
    "not_found": "The requested resource was not found.",
    "bad_request": "The request was malformed or missing required fields.",
    "unauthorized": "Authentication is required to access this resource.",
    "forbidden": "You do not have permission to access this resource.",
    "internal": "An unexpected error occurred. Please try again later.",
}

VALID_SORT_FIELDS = ["id", "name", "created_at", "updated_at"]
DEFAULT_SORT_FIELD = "id"
DEFAULT_SORT_ORDER = "asc"
