from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base

# Import all models so they register with Base.metadata
from app.models import (  # noqa: F401
    DeviceModel, Customer, Location, DeviceInstance, MovementLog,
    ServicePlan, Subscription, WorkOrder, Invoice, AuditLog,
)

from app.routers import (
    device_models, customers, locations, devices, workflows, dashboard,
    service_plans, subscriptions, work_orders, invoices, provisioning, audit,
)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_TITLE, version="1.0.0")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create tables on startup
    Base.metadata.create_all(bind=engine)

    # Register routers — existing
    app.include_router(device_models.router)
    app.include_router(customers.router)
    app.include_router(locations.router)
    app.include_router(devices.router)
    app.include_router(workflows.router)
    app.include_router(dashboard.router)

    # Register routers — ISP ERP modules
    app.include_router(service_plans.router)
    app.include_router(subscriptions.router)
    app.include_router(work_orders.router)
    app.include_router(invoices.router)
    app.include_router(provisioning.router)
    app.include_router(audit.router)

    @app.get("/")
    def root():
        return {
            "message": "ISP ERP System API",
            "docs": "/docs",
            "dry_run_mode": settings.DRY_RUN_MODE,
        }

    return app


app = create_app()

