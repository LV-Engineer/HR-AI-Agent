from fastapi import APIRouter, Depends, Request

from app.core.agent import ask_agent
from app.core.rate_limit import limiter
from app.core.deps import get_current_user
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix='/query', tags=['query'])

@router.post('', response_model=QueryResponse)
@limiter.limit('10/minute')
async def query(request: Request, payload: QueryRequest, user_id: str = Depends(get_current_user)) -> QueryResponse:
    answer = await ask_agent(payload.question)
    return QueryResponse(answer=answer)