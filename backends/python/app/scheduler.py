from apscheduler.schedulers.background import BackgroundScheduler

from app import crud
from app.checker import check_url
from app.database import SessionLocal


scheduler = BackgroundScheduler()

def check_monitor(monitor_id: int):
    db = SessionLocal()

    try:
        monitor = crud.get_monitor(db, monitor_id)

        if monitor is None or not monitor.is_active:
            return

        result = check_url(monitor.url)

        crud.create_check_result(
            db,
            monitor.id,
            result
        )

    finally:
        db.close()

def schedule_monitor(monitor):
    scheduler.add_job(
        check_monitor,
        trigger="interval",
        seconds=monitor.interval_seconds,
        args=[monitor.id],
        id=f"monitor_{monitor.id}",
        replace_existing=True
    )

def remove_monitor_schedule(monitor_id: int):
    job_id = f"monitor_{monitor_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

def load_monitors():
    db = SessionLocal()

    try:
        monitors = crud.get_monitors(db)

        for monitor in monitors:
            if monitor.is_active:
                schedule_monitor(monitor)

    finally:
        db.close()

def start_scheduler():
    scheduler.start()
    load_monitors()


def stop_scheduler():
    scheduler.shutdown()