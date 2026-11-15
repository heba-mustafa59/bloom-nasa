"""Restricted optional LLM adapter. Scientific numbers NEVER originate from model text.

Only public annual area-level observations and selected hypothesis are sent.
Private field observations, precise locations and user-uploaded photos are excluded.
"""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .living_data import MissionData
from .living_missions import explain_investigation, HYPOTHESES

KEYS = ("plausible", "counter_evidence", "unknown", "next_data")


def connected_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or None


def interrogate(data: MissionData, area: str, hypothesis: str, years: tuple[int, int],
                *, key: str | None = None, model: str | None = None,
                requester=None) -> dict:
    """Return validated deterministic facts and optionally four bounded LLM comments.

    A failed remote request returns a clearly labeled fallback, never fabricated model text.
    requester may be injected by tests. Call only after explicit user consent.
    """
    facts = explain_investigation(data, area, hypothesis, years)
    secret = key or connected_key()
    if not secret:
        return {**facts, "llm_status": "not_connected", "llm_notes": None}
    if hypothesis not in HYPOTHESES:
        raise ValueError("Unknown hypothesis")
    observations = [
        {"year": y, "ndvi": data.observation(area, y)["ndvi"],
         "gpm_polygon_rain_mm": data.observation(area, y)["gpm_rainfall_mm"]}
        for y in range(years[0], years[1] + 1)
    ]
    system = (
        "You are a scientific hypothesis critic. Supplied context is annual polygon-mean "
        "vegetation and rainfall, with source verification pending unless explicitly verified. "
        "Never assert causation, irrigation records, crops, or temperature readings. "
        "Do not mention any numerical values, years, percentages, scores or measurements in "
        "your free-text fields. No external factual claims. Be concise, "
        "critical and explain what evidence is missing. Output only the specified JSON."
    )
    schema = {
        "type": "object",
        "properties": {name: {"type": "string"} for name in KEYS},
        "required": list(KEYS), "additionalProperties": False,
    }
    payload = {
        "model": model or os.environ.get("BLOOM_AI_MODEL", "gpt-4.1-mini"),
        "instructions": system,
        "input": json.dumps({
            "region": area, "hypothesis": HYPOTHESES[hypothesis],
            "source_verification": data.verification,
            "observations": observations,
            "user_uploaded_data": "NOT PROVIDED",
        }, separators=(",", ":")),
        "store": False,
        "max_output_tokens": 350,
        "text": {"format": {"type": "json_schema", "name": "bloom_explanation",
                            "strict": True, "schema": schema}},
    }
    try:
        if requester is None:
            def requester(body):
                req = Request(
                    "https://api.openai.com/v1/responses",
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Authorization": f"Bearer {secret}",
                             "Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=20) as response:
                    return json.load(response)
        response = requester(payload)
        messages = response.get("output", [])
        text = next(
            part.get("text")
            for item in messages if item.get("type") == "message"
            for part in item.get("content", [])
            if part.get("type") == "output_text" and isinstance(part.get("text"), str)
        )
        notes = json.loads(text)
        if (not isinstance(notes, dict) or set(notes) != set(KEYS)
                or any(not isinstance(notes[key], str) or not (8 <= len(notes[key]) <= 600)
                       or re.search(r"\\d", notes[key]) for key in KEYS)):
            raise ValueError("Model output failed scientific safety validation")
        return {**facts, "engine": "Deterministic facts + restricted connected model critique",
                "llm_status": "connected", "llm_notes": notes}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, StopIteration,
            KeyError, TypeError, json.JSONDecodeError):
        return {**facts, "llm_status": "unavailable_fallback", "llm_notes": None}
