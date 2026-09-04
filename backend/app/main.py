from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import init_db
from app.api import health, inspection, auth, rules, products, dashboard, reports

app = FastAPI(
    title=settings.app_name,
    description="Automated Legal Metrology Compliance Checking System (SIH26034) - Backend API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(inspection.router, prefix="/api", tags=["Inspection"])
app.include_router(rules.router, prefix="/api", tags=["Rules"])
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])


@app.get("/")
def root():
    return {"message": f"{settings.app_name} is running.", "docs": "/docs"}
