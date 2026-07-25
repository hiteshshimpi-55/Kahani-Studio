from fastapi import APIRouter

from app.api.dependencies import db as db_deps

get_db = db_deps.get_db

__all__ = ["get_db"]
