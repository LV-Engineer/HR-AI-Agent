from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.reports import ReportNotFoundError, delete_report, list_reports, resolve_report_path
from app.schemas.report import ReportSummary

router = APIRouter(prefix='/reports', tags=['reports'])

@router.get('', response_model=list[ReportSummary], dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def list_all_reports(request: Request) -> list[ReportSummary]:
    return [ReportSummary.model_validate(r._asdict()) for r in list_reports()]

@router.get('/{filename}', dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def view_report(request: Request, filename: str) -> FileResponse:
    try:
        file_path = resolve_report_path(filename)
    except ReportNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Report not found')
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename,
        content_disposition_type='inline',
    )

@router.delete('/{filename}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
@limiter.limit('10/minute')
def delete_report_endpoint(request: Request, filename: str) -> None:
    try:
        delete_report(filename)
    except ReportNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Report not found')
