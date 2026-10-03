from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, battleground, conversations, health, query

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(query.router, tags=["Text-to-SQL Query"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(conversations.router, prefix="/conversations", tags=["Chat History"])
api_v1_router.include_router(battleground.router, prefix="/battleground", tags=["SQL Battleground"])
api_v1_router.include_router(admin.router, prefix="/admin", tags=["Admin & Data Ingestion"])
