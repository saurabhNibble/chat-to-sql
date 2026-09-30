from fastapi import APIRouter, Depends, status

from app.api.deps import get_optional_user, get_query_service
from app.models.auth import UserProfile
from app.models.query import ErrorResponse, QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate Natural Language to SQL and Execute",
    description=(
        "Translates a natural language prompt into an executable read-only SQL statement. "
        "If the prompt is ambiguous, returns clarification question and options. "
        "Otherwise, safely executes the query and returns columns and row results."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Successful execution or clarification request",
            "model": QueryResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Validation or safety check failed",
            "model": ErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Database execution error",
            "model": ErrorResponse,
        },
    },
)
def handle_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
    current_user: UserProfile | None = Depends(get_optional_user),
) -> QueryResponse:
    user_id = current_user.id if current_user else None
    return query_service.process_query(
        request.prompt,
        request.conversation_id,
        user_id=user_id,
    )
