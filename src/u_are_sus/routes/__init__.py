from importlib import import_module

from fastapi import APIRouter, FastAPI

ROUTER_MODULE_MANIFEST = ["join"]

routers: list[APIRouter] = [
    getattr(import_module(f"routes.{i}"), "router") for i in ROUTER_MODULE_MANIFEST
]


def include_routers(app: FastAPI, routers: list[APIRouter] = routers):
    for router in routers:
        app.include_router(router)
