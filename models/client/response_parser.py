import json
import logging
import re
from dataclasses import fields as dataclass_fields
from typing import Any, Type, TypeVar

T = TypeVar("T")

logger = logging.getLogger("societas.ai.parser")


class ParseError(Exception):
    pass


def _extract_json(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    return text


def parse_response(text: str, target_cls: Type[T], max_retries: int = 2) -> T:
    for attempt in range(max_retries):
        try:
            cleaned = _extract_json(text)
            data = json.loads(cleaned)
            if target_cls is dict:
                return data
            return _hydrate_dataclass(target_cls, data)
        except (json.JSONDecodeError, TypeError, ValueError, KeyError) as e:
            logger.warning("parse attempt %d/%d failed: %s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise ParseError(
                    f"failed after {max_retries} attempts: {e}"
                ) from e


def _hydrate_dataclass(cls: Type[T], data: dict) -> T:
    field_set = {f.name for f in dataclass_fields(cls)}
    kwargs = {k: v for k, v in data.items() if k in field_set}
    return cls(**kwargs)
