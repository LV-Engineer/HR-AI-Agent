from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.schemas.policy import HrPolicyResponse
from app.services.policy import HrPolicyNotFoundError, PolicyService, UnsupportedFileTypeError

router = APIRouter(prefix='/policies', tags=['policies'])

@router.post('', response_model=HrPolicyResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
async def upload_policy(
    request: Request,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> HrPolicyResponse:
    try:
        return PolicyService(db).upload_policy(
            title=title,
            filename=file.filename or '',
            file_bytes=await file.read(),
        )
    except UnsupportedFileTypeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only PDF files are supported',
        )

@router.get('', response_model=list[HrPolicyResponse], dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def list_policies(
    request: Request,
    db: Session = Depends(get_db),
) -> list[HrPolicyResponse]:
    return PolicyService(db).list_policies()

@router.get('/{policy_id}', dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def view_policy(
    request: Request,
    policy_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        file_path, title = PolicyService(db).get_policy_file(policy_id)
    except HrPolicyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Policy not found')
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=f'{title}.pdf',
        content_disposition_type='inline',
    )

@router.delete('/{policy_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def delete_policy(
    request: Request,
    policy_id: int,
    db: Session = Depends(get_db),
) -> None:
    try:
        PolicyService(db).delete_policy(policy_id)
    except HrPolicyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Policy not found')