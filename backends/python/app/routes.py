from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app import crud
from app.schemas import (
    MonitorCreate,
    MonitorUpdate,
    MonitorResponse,
    CheckResultCreateResponse,
    CheckResultResponse,
    ErrorResponse
)
from app.checker import check_url
from app.scheduler import schedule_monitor, remove_monitor_schedule


router = APIRouter(prefix="/api/monitors", tags=["Monitors"])


@router.get("", response_model=list[MonitorResponse])
def read_monitors(db: Session = Depends(get_db)):
    return crud.get_monitors(db)


@router.post("", response_model=MonitorResponse, status_code=201)
def create_monitor(
    monitor_data: MonitorCreate,
    db: Session = Depends(get_db)
):
    monitor = crud.create_monitor(db, monitor_data)

    if monitor.is_active:
        schedule_monitor(monitor)

    return monitor

@router.get(
    "/{monitor_id}",
    response_model=MonitorResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Monitor not found"
        }
    }
)
def read_monitor(
    monitor_id: int,
    db: Session = Depends(get_db)
):
    monitor = crud.get_monitor(db, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    return monitor


@router.patch(
    "/{monitor_id}",
    response_model=MonitorResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Monitor not found"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
def update_monitor(
    monitor_id: int,
    update_data: MonitorUpdate,
    db: Session = Depends(get_db)
):
    monitor = crud.get_monitor(db, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    changes = update_data.model_dump(
        exclude_unset=True,
        mode="json"
    )

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one field must be provided"
        )

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{field} cannot be null"
            )

    updated_monitor = crud.update_monitor(db, monitor, changes)

    if updated_monitor.is_active:
        schedule_monitor(updated_monitor)
    else:
        remove_monitor_schedule(updated_monitor.id)

    return updated_monitor

@router.delete(
    "/{monitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Monitor not found"
        }
    }
)
def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db)
):
    monitor = crud.get_monitor(db, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    remove_monitor_schedule(monitor_id)
    crud.delete_monitor(db, monitor)

@router.post(
    "/{monitor_id}/check",
    response_model=CheckResultCreateResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Monitor not found"
        }
    }
)

def run_monitor_check(
    monitor_id: int,
    db: Session = Depends(get_db)
):
    monitor = crud.get_monitor(db, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    result = check_url(monitor.url)

    saved_result = crud.create_check_result(
        db,
        monitor.id,
        result
    )

    return saved_result

@router.get(
    "/{monitor_id}/history",
    response_model=list[CheckResultResponse],
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Monitor not found"
        }
    }
)
def read_monitor_history(
    monitor_id: int,
    db: Session = Depends(get_db)
):
    monitor = crud.get_monitor(db, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    return crud.get_check_results(db, monitor_id)