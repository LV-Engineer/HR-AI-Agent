from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.schemas.job_requirement import (
    JobRequirementCreateRequest,
    JobRequirementResponse,
    JobRequirementSummary,
    JobRequirementUpdateRequest,
)
from app.services.job_requirement import JobRequirementNotFoundError, JobRequirementService

router = APIRouter(prefix='/job-requirements', tags=['job-requirements'])

@router.post('', response_model=JobRequirementResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def create_job_requirement(
    request: Request,
    payload: JobRequirementCreateRequest,
    db: Session = Depends(get_db),
) -> JobRequirementResponse:
    return JobRequirementService(db).create_job_requirement(payload.title, payload.content)

@router.get('', response_model=list[JobRequirementSummary], dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def list_job_requirements(
    request: Request,
    db: Session = Depends(get_db),
) -> list[JobRequirementSummary]:
    return JobRequirementService(db).list_job_requirements()

@router.get('/{job_requirement_id}', response_model=JobRequirementResponse, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def get_job_requirement(
    request: Request,
    job_requirement_id: int,
    db: Session = Depends(get_db),
) -> JobRequirementResponse:
    try:
        return JobRequirementService(db).get_job_requirement(job_requirement_id)
    except JobRequirementNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job requirement not found')

@router.patch('/{job_requirement_id}', response_model=JobRequirementResponse, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def update_job_requirement(
    request: Request,
    job_requirement_id: int,
    payload: JobRequirementUpdateRequest,
    db: Session = Depends(get_db),
) -> JobRequirementResponse:
    try:
        return JobRequirementService(db).update_job_requirement(job_requirement_id, payload.title, payload.content)
    except JobRequirementNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job requirement not found')

@router.delete('/{job_requirement_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def delete_job_requirement(
    request: Request,
    job_requirement_id: int,
    db: Session = Depends(get_db),
) -> None:
    try:
        JobRequirementService(db).delete_job_requirement(job_requirement_id)
    except JobRequirementNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job requirement not found')
