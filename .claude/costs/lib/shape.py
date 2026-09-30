"""Reading untyped JSON — transcript records, rows, the rate table — into
checked values, and writing dataclasses back out as the rows' JSON.

A field that is absent and one that is an explicit `null` read the same: some
transcript fields arrive as `null` rather than being left out, and both mean
there is nothing to read. Every error names where the value was, down to the
transcript line, so a changed record shape is found rather than guessed at.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from typing import Any, Callable, Dict, Iterator, Mapping, Optional, Tuple, TypeVar


class ShapeError(ValueError):
    """A record, row or rate table that is not the shape the ledger reads."""


T = TypeVar("T")


def mistyped(where: str, key: str, value: Any, wanted: str) -> ShapeError:
    return ShapeError(f"{where}: `{key}` is {type(value).__name__}, not {wanted}")


def is_number(value: Any) -> bool:
    """JSON's numbers, less `bool`, which Python counts as an `int`."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def json_lines(text: str, label: str) -> Iterator[Tuple[str, str, Any]]:
    """`(where, line, record)` for each non-blank line of a JSONL file."""
    for number, line in enumerate(text.split("\n"), start=1):
        if line.strip() == "":
            continue
        where = f"{label} line {number}"
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ShapeError(f"{where}: not JSON ({error})") from error
        yield where, line, record


def read_number(obj: Mapping[str, Any], key: str, where: str) -> Optional[float]:
    value = obj.get(key)
    if value is not None and not is_number(value):
        raise mistyped(where, key, value, "a number")
    return value


def read_count(obj: Mapping[str, Any], key: str, where: str) -> Optional[int]:
    value = obj.get(key)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if value is not None and not (is_number(value) and isinstance(value, int)):
        raise mistyped(where, key, value, "a whole number")
    return value


def read_string(obj: Mapping[str, Any], key: str, where: str) -> Optional[str]:
    value = obj.get(key)
    if value is not None and not isinstance(value, str):
        raise mistyped(where, key, value, "a string")
    return value


def read_object(obj: Mapping[str, Any], key: str, where: str) -> Optional[Dict[str, Any]]:
    value = obj.get(key)
    if value is not None and not isinstance(value, dict):
        raise mistyped(where, key, value, "an object")
    return value


def required(
    read: Callable[[Mapping[str, Any], str, str], Optional[T]],
    obj: Mapping[str, Any],
    key: str,
    where: str,
) -> T:
    value = read(obj, key, where)
    if value is None:
        raise ShapeError(f"{where}: `{key}` is missing")
    return value


def camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def to_json(value: Any) -> Any:
    """A dataclass tree as the JSON a row is written as, keys in camelCase."""
    if is_dataclass(value) and not isinstance(value, type):
        return {camel(f.name): to_json(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {key: to_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_json(item) for item in value]
    return value
