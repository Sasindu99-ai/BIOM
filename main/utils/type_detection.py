"""Shared value-based data type detection for StudyVariable.

Used both when previewing a data import (StudyService) and when creating
variables during an import job (DataImportService), so the two paths can
never disagree on a column's detected type. Also used by the
`fix_variable_types` management command to re-derive types for variables
that already have data in the database.
"""
import re
from collections.abc import Iterable

__all__ = ['detect_variable_type', 'field_for_type']

# Tokens that represent "no value" and must not influence type detection.
_MISSING_TOKENS = {
    '', 'na', 'n/a', 'n.a.', '#n/a', 'null', 'none', 'nan', 'nil', '-', '--', 'unknown', '?',
}

# Textual boolean tokens. Deliberately excludes bare '0'/'1' here - those are
# only treated as boolean when they are the *only* two distinct values a
# column ever takes (see detect_variable_type), otherwise a numeric column
# that happens to sample two 0/1 rows would be misclassified as BOOLEAN.
_BOOLEAN_WORD_TOKENS = {'true', 'false', 'yes', 'no', 'y', 'n'}
_BOOLEAN_NUMERIC_TOKENS = {'0', '1'}

_DATE_PATTERNS = [
    re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$'),                     # 2024-01-05, 2024/1/5
    re.compile(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$'),                     # 05-01-2024
    re.compile(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2}$'),                     # 05-01-24
    re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}[T ]\d{1,2}:\d{2}(:\d{2})?$'),  # ISO datetime
    re.compile(r'^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}$'),                 # 5 January 2024
    re.compile(r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}$'),               # January 5, 2024
]


def _clean(raw_values: Iterable) -> list[str]:
    values = (str(v).strip() for v in raw_values)
    return [v for v in values if v and v.lower() not in _MISSING_TOKENS]


def _is_number(value: str) -> bool:
    try:
        float(value.replace(',', ''))
    except (ValueError, TypeError):
        return False
    return True


def _is_date(value: str) -> bool:
    return any(pattern.match(value) for pattern in _DATE_PATTERNS)


def detect_variable_type(raw_values: Iterable) -> str:
    """Infer a StudyVariableType choice ('NUMBER'/'DATE'/'BOOLEAN'/'TEXT') from real values.

    Missing/blank-like tokens are ignored. An empty or all-missing input
    defaults to TEXT, matching the field's model default.
    """
    values = _clean(raw_values)
    if not values:
        return 'TEXT'

    distinct_lower = {v.lower() for v in values}

    if distinct_lower <= _BOOLEAN_WORD_TOKENS:
        return 'BOOLEAN'
    if distinct_lower <= _BOOLEAN_NUMERIC_TOKENS and len(distinct_lower) == len(_BOOLEAN_NUMERIC_TOKENS):
        return 'BOOLEAN'

    if all(_is_number(v) for v in values):
        return 'NUMBER'

    if all(_is_date(v) for v in values):
        return 'DATE'

    return 'TEXT'


def field_for_type(variable_type: str) -> str:
    """Map a StudyVariableType to a compatible StudyVariableField widget choice.

    StudyVariableField has no NUMBER/BOOLEAN widgets, so those (and TEXT)
    render as plain text input; only DATE gets its own widget.
    """
    return 'DATE' if variable_type == 'DATE' else 'TEXT'
