import time

import httpx

REQUEST_TIMEOUT = 10

def check_url(url: str) -> dict:
    start_time = time.perf_counter()

    try:
        response = httpx.get(
            url,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True
        )

        response_time = time.perf_counter() - start_time

        return {
            "status": "UP" if response.is_success else "DOWN",
            "status_code": response.status_code,
            "response_time_ms": round(response_time * 1000),
            "error_message": None
        }

    except Exception as error:
        response_time = time.perf_counter() - start_time

        return {
            "status": "DOWN",
            "status_code": None,
            "response_time_ms": round(response_time * 1000),
            "error_message": str(error)
        }