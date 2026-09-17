import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.schemas.candidate import CandidateCVResponse
from app.services.candidate import CandidateService, UnsupportedFileTypeError, CandidateCVNotFoundError

router = APIRouter(prefix='/candidates', tags=['candidates'])

@router.post('/cv', response_model=CandidateCVResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit('10/minute')
async def upload_cv(
    request: Request,
    candidate_name: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CandidateCVResponse:
    try:
        return CandidateService(db).upload_cv(
            candidate_name=candidate_name,
            filename=file.filename or '',
            file_bytes=await file.read(),
            uploaded_by=uuid.UUID(user_id)
        )
    except UnsupportedFileTypeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only PDF files are supported',
        )

@router.get('/cv', response_model=list[CandidateCVResponse], dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def list_cvs(
    request: Request,
    db: Session = Depends(get_db),
) -> list[CandidateCVResponse]:
    return CandidateService(db).list_cvs()

@router.get('/cv/{cv_id}', dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def view_cv(
    request: Request,
    cv_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        file_path, candidate_name = CandidateService(db).get_cv_file(cv_id)
    except CandidateCVNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='CV not found')
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=f'{candidate_name}.pdf',
        content_disposition_type='inline',
    )

@router.delete('/cv/{cv_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def delete_cv(
    request: Request,
    cv_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    try:
        CandidateService(db).delete_cv(cv_id)
    except CandidateCVNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='CV not found')