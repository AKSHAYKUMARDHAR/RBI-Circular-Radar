"""The model reader: Gemini over the notification's text, JSON constrained by the schema, answers cached.

Long directions (up to 83 pages) are cut to the pages that carry what's asked: the first three, then pages
with applicability, commencement, comment or deadline wording, up to MAX_PAGES. Every answer is cached on
disk by model, prompt version and document hash, so scoring variants never costs another request.
"""
import json
import os
import pathlib
import re
import time

from . import prompts
from .text import DATE_RE

MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "18"))
RPM = float(os.getenv("GEMINI_RPM", "8"))
# Page priority after the first three: commencement and applicability, then deadlines, then other date words.
CORE_WORDS = re.compile(r"applicab|appl(?:y|ies) to|come into (?:force|effect)|commencement|comments", re.I)
DEADLINE_WORDS = re.compile(r"(?:on or before|not later than|no later than|latest by|by|before|within)\s+(?:the\s+)?"
                            + DATE_RE.pattern, re.I)
KEY_WORDS = re.compile(r"effective|with immediate effect|from the date of|repeal", re.I)


class LLMError(Exception):
    pass


class QuotaExhausted(LLMError):
    """The day's free quota is used up; retrying today won't help."""


def select_pages(pages: list[str], max_pages: int = MAX_PAGES) -> list[int]:
    n = len(pages)
    if n <= max_pages:
        return list(range(1, n + 1))
    keep = [i for i in (1, 2, 3) if i <= n]
    for pat in (CORE_WORDS, DEADLINE_WORDS, KEY_WORDS):
        for i in range(1, n + 1):
            if len(keep) >= max_pages:
                break
            if i not in keep and pat.search(pages[i - 1]):
                keep.append(i)
    return sorted(keep)


class GeminiReader:
    def __init__(self, model: str | None = None, cache_dir: str | os.PathLike | None = None):
        from google import genai

        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        self.cache_dir = pathlib.Path(cache_dir) if cache_dir else None
        self._next_at = 0.0

    def _cache_path(self, doc_id: str, sha: str, attempt: int) -> pathlib.Path | None:
        if not self.cache_dir:
            return None
        return self.cache_dir / self.model / f"{doc_id}.{prompts.VERSION}.{sha[:12]}.{attempt}.json"

    def read(self, doc_id: str, sha: str, title: str, issued: str | None, pages: list[str], attempt: int = 0) -> dict:
        path = self._cache_path(doc_id, sha, attempt)
        if path and path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        keep = select_pages(pages)
        answer, usage = self._call(prompts.user_message(title, issued, pages, keep))
        out = {"model": self.model, "prompt_version": prompts.VERSION, "doc": doc_id, "sha256": sha,
               "pages_shown": keep, "usage": usage, "answer": answer}
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        return out

    def _call(self, user: str) -> tuple[dict, dict]:
        from google.genai import errors, types

        cfg = types.GenerateContentConfig(
            system_instruction=prompts.SYSTEM, response_mime_type="application/json",
            response_json_schema=prompts.SCHEMA, temperature=0.0, max_output_tokens=8000,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
        delay = 10.0
        for attempt in range(MAX_RETRIES + 1):
            wait = self._next_at - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._next_at = time.monotonic() + 60.0 / RPM
            try:
                resp = self.client.models.generate_content(model=self.model, contents=[user], config=cfg)
                um = resp.usage_metadata
                usage = {"input_tokens": getattr(um, "prompt_token_count", 0) or 0,
                         "output_tokens": (getattr(um, "candidates_token_count", 0) or 0)
                         + (getattr(um, "thoughts_token_count", 0) or 0)}
                if not resp.text:
                    raise LLMError("empty response")
                return json.loads(resp.text), usage
            except errors.APIError as e:
                details = (getattr(e, "details", None) or {}).get("error", {}).get("details", [])
                day = [v for d in details for v in d.get("violations", []) if "PerDay" in v.get("quotaId", "")]
                if day:
                    raise QuotaExhausted(f"daily quota used up for {self.model} "
                                         f"({day[0].get('quotaId')}, limit {day[0].get('quotaValue', '?')})") from e
                if getattr(e, "code", None) not in (429, 500, 502, 503, 504) or attempt == MAX_RETRIES:
                    raise LLMError(f"Gemini {getattr(e, 'code', '?')}: {str(e)[:200]}") from e
            except json.JSONDecodeError as e:
                if attempt == MAX_RETRIES:
                    raise LLMError(f"invalid JSON: {e}") from e
            except LLMError:
                raise
            except Exception as e:   # dropped connection, timeout
                if attempt == MAX_RETRIES:
                    raise LLMError(f"transport error: {type(e).__name__}: {str(e)[:200]}") from e
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
        raise LLMError("unreachable")
