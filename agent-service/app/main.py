from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.auth.routes import router as auth_router
from app.conversations.routes import router as conversations_router, query_router
from app.candidates.routes import router as candidates_router
from app.policies.routes import router as policies_router
from app.job_requirements.routes import router as job_requirements_router
from app.reports.routes import router as reports_router
from app.core.config import settings
from app.core.rate_limit import limiter

app = FastAPI(title='Agent-Service')
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def rate_limit_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RateLimitExceeded)
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth_router)
app.include_router(query_router)
app.include_router(conversations_router)
app.include_router(candidates_router)
app.include_router(policies_router)
app.include_router(job_requirements_router)
app.include_router(reports_router)
