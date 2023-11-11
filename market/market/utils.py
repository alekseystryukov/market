from typing import List, Optional


def to_bool(value: Optional[str]) -> bool:
    return (value or '').lower() in ('1', 'true')


def to_list(value: Optional[str], separator: str = ',') -> List[str]:
    return value.split(separator) if value else []
