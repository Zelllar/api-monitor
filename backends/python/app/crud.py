from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.models import Monitor, CheckResult
from app.schemas import MonitorCreate


def get_monitors(db: Session):
    statement = select(Monitor).order_by(Monitor.id)
    return db.scalars(statement).all()

def create_monitor(db: Session, monitor_data: MonitorCreate):
    monitor = Monitor(
        name=monitor_data.name,
        url=str(monitor_data.url),
        interval_seconds=monitor_data.interval_seconds
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    return monitor

def get_monitor(db: Session, monitor_id: int):
    statement = select(Monitor).where(Monitor.id == monitor_id)
    return db.scalars(statement).first()

def update_monitor(db: Session, monitor: Monitor, update_data: dict):
    for field, value in update_data.items():
        setattr(monitor, field, value)

    monitor.updated_at = func.now()

    db.commit()
    db.refresh(monitor)

    return monitor

def delete_monitor(db: Session, monitor: Monitor):
    db.delete(monitor)
    db.commit()

def create_check_result(db: Session, monitor_id: int, result: dict):
    check_result = CheckResult(
        monitor_id=monitor_id,
        status=result["status"],
        status_code=result["status_code"],
        response_time_ms=result["response_time_ms"],
        error_message=result["error_message"]
    )

    db.add(check_result)
    db.commit()
    db.refresh(check_result)

    return check_result

def get_check_results(db: Session, monitor_id: int, limit: int = 50):
    statement = (
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id)
        .order_by(desc(CheckResult.checked_at))
        .limit(limit)
    )

    return db.scalars(statement).all()