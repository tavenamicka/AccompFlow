from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admin, alertes, auth, clients, documents, interventions, me, rapports, users
from app.config import settings
from app.core.limiter import limiter

# /docs, /redoc, /openapi.json désactivés en production : si ce prototype
# est un jour déployé en LAN sans vhost public dessus, ces routes y seraient
# réellement atteignables — même durcissement que Recueil/ForfaitFlow/
# espace-client (INFRASTRUCTURE.md §11). Prototype non déployé à ce stade,
# ENVIRONMENT=development par défaut (docker-compose.yml).
docs_kwargs = (
    {"docs_url": None, "redoc_url": None, "openapi_url": None}
    if settings.environment == "production"
    else {}
)

app = FastAPI(title="AccompFlow API", **docs_kwargs)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(admin.router)
app.include_router(clients.router)
app.include_router(interventions.router)
app.include_router(alertes.router)
app.include_router(rapports.router)
app.include_router(me.router)


@app.get("/health")
def health():
    return {"status": "ok"}
