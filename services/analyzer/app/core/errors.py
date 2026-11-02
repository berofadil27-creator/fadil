"""Système d'erreurs : chaque erreur renvoie la même structure JSON, en français."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class VeyraError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def _body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(VeyraError)
    async def veyra_error(_: Request, exc: VeyraError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=_body(
            "invalid_request", "La demande est incomplète ou mal formée."))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        messages = {404: "Adresse introuvable.", 405: "Méthode non autorisée."}
        return JSONResponse(status_code=exc.status_code, content=_body(
            "http_error", messages.get(exc.status_code, str(exc.detail))))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        return JSONResponse(status_code=500, content=_body(
            "internal_error", "Une erreur inattendue est survenue. Réessayez plus tard."))
