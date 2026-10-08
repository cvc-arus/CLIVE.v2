from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from simpro_mock.filtering import UnknownFilterParameterError
from simpro_mock.middleware import BearerAuthMiddleware
from simpro_mock.ordering import UnknownOrderFieldError
from simpro_mock.routers import api_router, health_router, token_router

app = FastAPI(title="Simpro Mock API", version="0.1.0")

app.add_middleware(BearerAuthMiddleware)


@app.exception_handler(UnknownFilterParameterError)
async def unknown_filter_handler(
    request: Request, exc: UnknownFilterParameterError
) -> JSONResponse:
    """Turn an unrecognised filter parameter into a 400.

    One handler rather than a try/except in each of the 25 route functions,
    and it keeps `filtering.py` free of any FastAPI import. Before this, an
    unmapped filter was ignored, so a caller received unfiltered data and
    believed it was filtered.
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "parameter": exc.name,
            "resource": exc.model_name,
            "filterable": exc.allowed,
        },
    )


@app.exception_handler(UnknownOrderFieldError)
async def unknown_order_field_handler(
    request: Request, exc: UnknownOrderFieldError
) -> JSONResponse:
    """Turn an unorderable ``orderby`` field into a 400.

    Same reasoning as the filter handler above: returning 200 with unsorted
    rows would leave the caller unable to tell from the response that the
    parameter did nothing.
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "field": exc.name,
            "resource": exc.model_name,
            "orderable": exc.allowed,
        },
    )


# Make sure all three routers are registered!
app.include_router(health_router)
app.include_router(token_router)
app.include_router(api_router)
