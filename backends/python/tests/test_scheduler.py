from unittest.mock import patch
from app.scheduler import schedule_monitor, check_monitor
from app.scheduler import remove_monitor_schedule
from app.scheduler import check_monitor
from app.scheduler import load_monitors
from app.scheduler import start_scheduler
from app.scheduler import stop_scheduler

def test_schedule_monitor():
    monitor = type(
        "Monitor",
        (),
        {
            "id": 1,
            "interval_seconds": 60
        }
    )()

    with patch("app.scheduler.scheduler.add_job") as mock_add_job:
        schedule_monitor(monitor)

    mock_add_job.assert_called_once_with(
        check_monitor,
        trigger="interval",
        seconds=60,
        args=[1],
        id="monitor_1",
        replace_existing=True
    )

def test_remove_monitor_schedule():
    with (
        patch("app.scheduler.scheduler.get_job") as mock_get_job,
        patch("app.scheduler.scheduler.remove_job") as mock_remove_job
    ):
        mock_get_job.return_value = True

        remove_monitor_schedule(1)

    mock_get_job.assert_called_once_with("monitor_1")
    mock_remove_job.assert_called_once_with("monitor_1")

def test_remove_monitor_schedule_not_found():
    with (
        patch("app.scheduler.scheduler.get_job") as mock_get_job,
        patch("app.scheduler.scheduler.remove_job") as mock_remove_job
    ):
        mock_get_job.return_value = None

        remove_monitor_schedule(999)

    mock_get_job.assert_called_once_with("monitor_999")
    mock_remove_job.assert_not_called()

def test_check_monitor():
    monitor = type(
        "Monitor",
        (),
        {
            "id": 1,
            "url": "https://example.com",
            "is_active": True
        }
    )()

    result = {
        "status": "UP",
        "status_code": 200,
        "response_time_ms": 150,
        "error_message": None
    }

    with (
        patch("app.scheduler.SessionLocal") as mock_session,
        patch("app.scheduler.crud.get_monitor") as mock_get_monitor,
        patch("app.scheduler.check_url") as mock_check_url,
        patch("app.scheduler.crud.create_check_result") as mock_create_result
    ):
        db = mock_session.return_value
        mock_get_monitor.return_value = monitor
        mock_check_url.return_value = result

        check_monitor(1)

    mock_get_monitor.assert_called_once_with(db, 1)
    mock_check_url.assert_called_once_with("https://example.com")
    mock_create_result.assert_called_once_with(db, 1, result)
    db.close.assert_called_once()


def test_check_monitor_not_found():
    with (
        patch("app.scheduler.SessionLocal") as mock_session,
        patch("app.scheduler.crud.get_monitor") as mock_get_monitor,
        patch("app.scheduler.check_url") as mock_check_url,
        patch("app.scheduler.crud.create_check_result") as mock_create_result
    ):
        db = mock_session.return_value
        mock_get_monitor.return_value = None

        check_monitor(999)

    mock_get_monitor.assert_called_once_with(db, 999)
    mock_check_url.assert_not_called()
    mock_create_result.assert_not_called()
    db.close.assert_called_once()


def test_check_monitor_inactive():
    monitor = type(
        "Monitor",
        (),
        {
            "id": 1,
            "url": "https://example.com",
            "is_active": False
        }
    )()

    with (
        patch("app.scheduler.SessionLocal") as mock_session,
        patch("app.scheduler.crud.get_monitor") as mock_get_monitor,
        patch("app.scheduler.check_url") as mock_check_url,
        patch("app.scheduler.crud.create_check_result") as mock_create_result
    ):
        db = mock_session.return_value
        mock_get_monitor.return_value = monitor

        check_monitor(1)

    mock_get_monitor.assert_called_once_with(db, 1)
    mock_check_url.assert_not_called()
    mock_create_result.assert_not_called()
    db.close.assert_called_once()

def test_load_monitors():
    active_monitor = type(
        "Monitor",
        (),
        {
            "id": 1,
            "interval_seconds": 60,
            "is_active": True
        }
    )()

    inactive_monitor = type(
        "Monitor",
        (),
        {
            "id": 2,
            "interval_seconds": 120,
            "is_active": False
        }
    )()

    with (
        patch("app.scheduler.SessionLocal") as mock_session,
        patch("app.scheduler.crud.get_monitors") as mock_get_monitors,
        patch("app.scheduler.schedule_monitor") as mock_schedule
    ):
        db = mock_session.return_value

        mock_get_monitors.return_value = [
            active_monitor,
            inactive_monitor
        ]

        load_monitors()

    mock_get_monitors.assert_called_once_with(db)
    mock_schedule.assert_called_once_with(active_monitor)
    db.close.assert_called_once()

def test_start_scheduler():
    with (
        patch("app.scheduler.scheduler.start") as mock_start,
        patch("app.scheduler.load_monitors") as mock_load
    ):
        start_scheduler()

    mock_start.assert_called_once()
    mock_load.assert_called_once()

def test_stop_scheduler():
    with patch("app.scheduler.scheduler.shutdown") as mock_shutdown:
        stop_scheduler()

    mock_shutdown.assert_called_once()