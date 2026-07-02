from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
import sqlite3
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from app.core.database import get_connection, init_db, utc_now


POLICY_NEWS_LIST_URL = "https://www.korea.kr/news/policyNewsList.do"
POLICY_NEWS_SOURCE = "대한민국 정책브리핑"
POLICY_NEWS_CATEGORY = "정책뉴스"
USER_AGENT = "DAY3-PolicyNewsCollector/1.0"
MAX_PAGES = 20
KST = timezone(timedelta(hours=9))


def _as_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_date(value: str) -> str | None:
    value = value.strip()
    patterns = [
        (r"(\d{4})\.(\d{2})\.(\d{2})", "{0}-{1}-{2}"),
        (r"(\d{4})-(\d{2})-(\d{2})", "{0}-{1}-{2}"),
        (r"(\d{4})/(\d{2})/(\d{2})", "{0}-{1}-{2}"),
    ]
    for pattern, template in patterns:
        match = re.search(pattern, value)
        if match:
            return template.format(*match.groups())
    return None


def _extract_date_from_text(text: str) -> str | None:
    return _normalize_date(text)


def _fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _page_url(page_index: int) -> str:
    if page_index <= 1:
        return POLICY_NEWS_LIST_URL
    return f"{POLICY_NEWS_LIST_URL}?{urlencode({'pageIndex': page_index})}"


def _extract_parent_text(anchor: Any) -> str:
    parent = anchor.find_parent(["li", "article", "div", "tr"]) or anchor.parent
    return _clean_text(parent.get_text(" ", strip=True)) if parent else ""


def _extract_list_items(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for anchor in soup.select('a[href*="policyNewsView.do?newsId="]'):
        href = anchor.get("href")
        if not href:
            continue

        url = urljoin(POLICY_NEWS_LIST_URL, href)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = _clean_text(anchor.get_text(" ", strip=True))
        if not title:
            title = _clean_text(anchor.get("title", ""))
        if not title:
            continue

        parent_text = _extract_parent_text(anchor)
        published_at = _extract_date_from_text(parent_text)
        items.append(
            {
                "title": title,
                "url": url,
                "list_date": published_at or "",
                "context_text": parent_text,
            }
        )

    return items


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in ("h1", "h2"):
        node = soup.select_one(selector)
        if node:
            title = _clean_text(node.get_text(" ", strip=True))
            if title and len(title) > 3:
                return title

    meta = soup.select_one('meta[property="og:title"], meta[name="title"]')
    if meta and meta.get("content"):
        return _clean_text(meta["content"])
    return ""


def _extract_published_at(soup: BeautifulSoup) -> str | None:
    candidates: list[str] = []

    for selector in ("time", "[datetime]", ".date", ".info", ".article-info", ".news-date"):
        for node in soup.select(selector):
            text = ""
            if node.has_attr("datetime"):
                text = str(node.get("datetime", ""))
            else:
                text = node.get_text(" ", strip=True)
            normalized = _extract_date_from_text(text)
            if normalized:
                candidates.append(normalized)

    if candidates:
        return candidates[0]

    text = soup.get_text(" ", strip=True)
    return _extract_date_from_text(text)


def _extract_summary(soup: BeautifulSoup) -> str:
    paragraphs: list[str] = []
    for node in soup.find_all(["p", "li"]):
        text = _clean_text(node.get_text(" ", strip=True))
        if len(text) < 30:
            continue
        if "무단 전재" in text or "이미지" in text or ("출처" in text and len(text) < 50):
            continue
        if text not in paragraphs:
            paragraphs.append(text)
        if len(paragraphs) >= 3:
            break

    summary = " ".join(paragraphs)
    if not summary:
        body_text = _clean_text(soup.get_text(" ", strip=True))
        summary = body_text

    return summary[:400]


def _fetch_article(url: str) -> dict[str, str]:
    html = _fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)
    published_at = _extract_published_at(soup)
    summary = _extract_summary(soup)
    return {
        "title": title,
        "url": url,
        "published_at": published_at or "",
        "summary": summary,
        "source": POLICY_NEWS_SOURCE,
        "category": POLICY_NEWS_CATEGORY,
    }


def _insert_run(target_date: str, mode: str) -> int:
    started_at = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO news_collection_runs
              (target_date, mode, status, fetched_count, inserted_count, duplicate_count, started_at)
            VALUES (?, ?, 'running', 0, 0, 0, ?)
            """,
            (target_date, mode, started_at),
        )
        connection.commit()
        return int(cursor.lastrowid)


def _update_run(
    run_id: int,
    *,
    status: str,
    fetched_count: int,
    inserted_count: int,
    duplicate_count: int,
    error_message: str | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE news_collection_runs
            SET status = ?, fetched_count = ?, inserted_count = ?, duplicate_count = ?,
                error_message = ?, finished_at = ?
            WHERE id = ?
            """,
            (status, fetched_count, inserted_count, duplicate_count, error_message, utc_now(), run_id),
        )
        connection.commit()


def has_completed_run(target_date: date | str, mode: str = "scheduled") -> bool:
    init_db()
    target = _as_date(target_date).isoformat()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM news_collection_runs
            WHERE target_date = ? AND mode = ? AND status = 'completed'
            ORDER BY id DESC
            LIMIT 1
            """,
            (target, mode),
        ).fetchone()
    return row is not None


def collect_policy_news(target_date: date | str, mode: str = "manual") -> dict[str, Any]:
    init_db()
    target = _as_date(target_date)
    target_text = target.isoformat()
    run_id = _insert_run(target_text, mode)

    fetched_count = 0
    inserted_count = 0
    duplicate_count = 0

    try:
        seen_urls: set[str] = set()
        should_stop = False

        for page_index in range(1, MAX_PAGES + 1):
            if should_stop:
                break

            html = _fetch_html(_page_url(page_index))
            list_items = _extract_list_items(html)
            if not list_items:
                break

            page_min_date: date | None = None

            for item in list_items:
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])

                article_list_date = _as_date(item["list_date"]) if item["list_date"] else None
                if article_list_date:
                    page_min_date = article_list_date if page_min_date is None else min(page_min_date, article_list_date)
                    if article_list_date < target:
                        should_stop = True
                        continue

                article = _fetch_article(item["url"])
                fetched_count += 1

                article_date = _as_date(article["published_at"]) if article["published_at"] else article_list_date
                if article_date is None:
                    continue

                page_min_date = article_date if page_min_date is None else min(page_min_date, article_date)
                if article_date < target:
                    should_stop = True
                    continue
                if article_date != target:
                    continue

                with get_connection() as connection:
                    exists = connection.execute(
                        "SELECT 1 FROM news_articles WHERE url = ?",
                        (article["url"],),
                    ).fetchone()
                    if exists:
                        duplicate_count += 1
                        continue

                    connection.execute(
                        """
                        INSERT INTO news_articles
                          (title, source, url, published_at, summary, category, collected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            article["title"],
                            article["source"],
                            article["url"],
                            article_date.isoformat(),
                            article["summary"],
                            article["category"],
                            utc_now(),
                        ),
                    )
                    connection.commit()
                    inserted_count += 1

            if page_min_date is not None and page_min_date < target:
                break

        _update_run(
            run_id,
            status="completed",
            fetched_count=fetched_count,
            inserted_count=inserted_count,
            duplicate_count=duplicate_count,
        )
        return {
            "run_id": run_id,
            "target_date": target_text,
            "mode": mode,
            "status": "completed",
            "fetched_count": fetched_count,
            "inserted_count": inserted_count,
            "duplicate_count": duplicate_count,
        }
    except Exception as exc:
        _update_run(
            run_id,
            status="failed",
            fetched_count=fetched_count,
            inserted_count=inserted_count,
            duplicate_count=duplicate_count,
            error_message=str(exc),
        )
        raise


def list_news_articles(target_date: date | str | None = None) -> list[dict[str, Any]]:
    init_db()
    target = _as_date(target_date).isoformat() if target_date else None
    with get_connection() as connection:
        if target:
            rows = connection.execute(
                """
                SELECT id, title, source, url, published_at, summary, category, collected_at
                FROM news_articles
                WHERE published_at = ?
                ORDER BY published_at DESC, id DESC
                """,
                (target,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, title, source, url, published_at, summary, category, collected_at
                FROM news_articles
                ORDER BY published_at DESC, id DESC
                """
            ).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def list_news_runs(limit: int = 20) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, target_date, mode, status, fetched_count, inserted_count, duplicate_count,
                   error_message, started_at, finished_at
            FROM news_collection_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [{key: row[key] for key in row.keys()} for row in rows]


def parse_manual_target_date(payload: dict[str, Any]) -> date:
    raw = str(payload.get("target_date", "")).strip()
    if not raw:
        return (datetime.now(KST).date() - timedelta(days=1))
    return date.fromisoformat(raw)
