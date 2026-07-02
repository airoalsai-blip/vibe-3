from __future__ import annotations

from datetime import datetime, timedelta, timezone
import threading
import time

from app.services.news_collector import collect_policy_news, has_completed_run


KST = timezone(timedelta(hours=9))


def _next_9am(value: datetime) -> datetime:
    candidate = value.replace(hour=9, minute=0, second=0, microsecond=0)
    if value >= candidate:
        candidate += timedelta(days=1)
    return candidate


def _sleep_until(moment: datetime) -> None:
    seconds = max(0.0, (moment - datetime.now(KST)).total_seconds())
    time.sleep(seconds)


def _run_catch_up() -> None:
    now = datetime.now(KST)
    if now.hour < 9:
        return

    target_date = (now.date() - timedelta(days=1))
    if has_completed_run(target_date, mode="scheduled"):
        return

    collect_policy_news(target_date, mode="scheduled")


def _scheduler_loop() -> None:
    while True:
        now = datetime.now(KST)
        next_run = _next_9am(now)
        if now < next_run:
            _sleep_until(next_run)
            now = datetime.now(KST)

        target_date = now.date() - timedelta(days=1)
        if not has_completed_run(target_date, mode="scheduled"):
            try:
                collect_policy_news(target_date, mode="scheduled")
            except Exception as exc:
                print(f"[scheduler] news collection failed for {target_date}: {exc}")

        _sleep_until(_next_9am(datetime.now(KST)))


def start_news_scheduler() -> threading.Thread:
    thread = threading.Thread(target=_scheduler_loop, name="news-collector", daemon=True)
    thread.start()
    return thread
