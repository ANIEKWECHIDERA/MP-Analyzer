from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from ..config import settings
from .normalization import normalize_key, normalize_text, parse_numeric

logger = logging.getLogger(__name__)


MONTH_NAME_TO_NUMBER = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

LEGACY_PATTERNS: dict[str, list[str]] = {
    "ZONES": [r"\bzones?\b"],
    "BRANCHES": [r"\bbranches?\b"],
    "PBT 2025 YTD ACHVD": [r"\bpbt\b.*\bytd\b.*\bach"],
    "PBT 2025 FULL YR BGT": [r"\bpbt\b.*\bfull\b.*\b(?:yr|year)\b.*\b(?:bgt|budget)\b", r"\bpbt\b.*\bbudget\b"],
    "PBT 2025 YOY VAR": [r"\bpbt\b.*\byoy\b.*\bvar"],
    "PBT Exp Run Rate": [r"\brun rate\b"],
    "PBT Cost to Income Ratio": [r"\bcost to income(?: ratio)?\b"],
    "PBT Mthly Var": [r"\bpbt\b.*\b(?:mthly|monthly)\b.*\bvar", r"\bmthly var\b"],
    "DDA 2025 FULL YR BGT": [r"\bdda\b.*\bfull\b.*\b(?:yr|year)\b.*\b(?:bgt|budget)\b"],
    "DDA YTD Variance": [r"\bdda\b.*\bytd\b.*\bvar"],
    "DDA MOM Variance": [r"\bdda\b.*\bmom\b.*\bvar"],
    "SAV 2025 FULL YR BGT": [r"\b(?:sav|savings)\b.*\bfull\b.*\b(?:yr|year)\b.*\b(?:bgt|budget)\b"],
    "SAV YTD Variance": [r"\b(?:sav|savings)\b.*\bytd\b.*\bvar"],
    "SAV MOM Variance": [r"\b(?:sav|savings)\b.*\bmom\b.*\bvar"],
    "FD 2025 FULL YR BGT": [r"\b(?:fd|fixed deposit)\b.*\bfull\b.*\b(?:yr|year)\b.*\b(?:bgt|budget)\b"],
    "FD YTD Variance": [r"\b(?:fd|fixed deposit)\b.*\bytd\b.*\bvar"],
    "FD MOM Variance": [r"\b(?:fd|fixed deposit)\b.*\bmom\b.*\bvar"],
    "DP 2025 FULL YR BGT": [r"\b(?:dp|total deposits|domiciliary deposits)\b.*\bfull\b.*\b(?:yr|year)\b.*\b(?:bgt|budget)\b"],
    "DP YTD Variance": [r"\b(?:dp|total deposits|domiciliary deposits)\b.*\bytd\b.*\bvar"],
    "TRA Loan to Dep": [r"\bloan to dep\b"],
    "TRA YTD Variance": [r"\btra\b.*\bytd\b.*\bvar"],
    "AB VAR": [r"\bab\b.*\bvar", r"\bvar\b.*\bab\b"],
    "AO C/A Opened - Funded": [r"\bao\b.*\bc a\b.*\bfunded"],
    "AO C/A Opened - Unfunded": [r"\bao\b.*\bc a\b.*\bunfunded"],
    "AO C/A Opened - Total": [r"\bao\b.*\bc a\b.*\btotal"],
    "AO S/A Opened - Funded": [r"\bao\b.*\bs a\b.*\bfunded"],
    "AO S/A Opened - Unfunded": [r"\bao\b.*\bs a\b.*\bunfunded"],
    "AO S/A Opened - Total": [r"\bao\b.*\bs a\b.*\btotal"],
    "CDS1 ACTIVE": [r"\bcds1\b.*\bactive"],
    "CDS2 ACTIVE": [r"\bcds2\b.*\bactive"],
    "CDS1 INACTIVE": [r"\bcds1\b.*\binactive"],
    "CDS2 INACTIVE": [r"\bcds2\b.*\binactive"],
    "CDS1 No. of Cards Issued": [r"\bcds1\b.*\bcards issued"],
    "CDS2 No. of Cards Issued": [r"\bcds2\b.*\bcards issued"],
    "POS ACTIVE": [r"\bpos\b.*\bactive"],
    "POS INACTIVE": [r"\bpos\b.*\binactive"],
    "POS NEWLY DEPLOYED": [r"\bpos\b.*\bnewly deployed"],
    "POS RETRIEVED": [r"\bpos\b.*\bretrieved"],
    "NXP YOY VAR": [r"\bnxp\b.*\byoy\b.*\bvar"],
    "TOTAL_DMT_ACT": [r"\btotal\b.*\bdmt\b.*\bact", r"\bdormant account\b"],
    "No. Reactivated DMT_ACT": [r"\bdmt act\b.*\bno\b.*\breactivated\b", r"\bno\b.*\breactivated\b", r"\breactivated\b.*\bno\b"],
    "% Reactivated DMT_ACT": [r"\bdmt act\b(?!.*\bno\b).*\breactivated\b", r"\bpercent\b.*\breactivated\b", r"\breactivated\b.*\bpercent\b", r"\b%\b.*\breactivated\b"],
}

DYNAMIC_FAMILY_SLOTS: dict[str, list[str]] = {
    "DDA": ["DDA May-25", "DDA Jun-25", "DDA Jul-25"],
    "SAV": ["SAV May-25", "SAV Jun-25", "SAV Jul-25"],
    "FD": ["FD May-25", "FD Jun-25", "FD Jul-25"],
    "DP": ["DP May-25", "DP Jun-25", "DP Jul-25"],
    "TRA": ["TRA May-25", "TRA Jun-25", "TRA Jul-25"],
    "CE": ["CE May-25", "CE Jun-25", "CE Jul-25"],
    "AOB": ["AOB May-25", "AOB Jun-25", "AOB Jul-25"],
    "NXP": ["NXP May-25", "NXP Jun-25", "NXP Jul-25"],
}

AB_SLOTS = ["AB Jun-25", "AB Jul-25"]
REQUIRED_FIELDS = ["ZONES", "BRANCHES", "PBT 2025 YTD ACHVD", "DDA Jul-25", "SAV Jul-25", "FD Jul-25", "DP Jul-25"]


@dataclass
class ParsedWorkbook:
    dataframe: pd.DataFrame
    header_row_index: int
    mapped_fields: dict[str, str]
    missing_fields: list[str]
    detected_period_label: str | None
    zones: list[str]
    structure_source_path: str | None = None


def _read_raw_table(path: str | Path) -> pd.DataFrame:
    path_str = str(path)
    if path_str.lower().endswith(".csv"):
        return pd.read_csv(path_str, header=None, dtype=str)
    return pd.read_excel(path_str, header=None, dtype=str)


def file_fingerprint(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    output: list[str] = []
    for header in headers:
        base = header or "unnamed"
        count = seen.get(base, 0) + 1
        seen[base] = count
        output.append(base if count == 1 else f"{base}__{count}")
    return output


def _detect_header_row(raw: pd.DataFrame) -> int:
    best_index = 0
    best_score = -1
    for idx in range(min(len(raw), 12)):
        row_values = [normalize_key(value) for value in raw.iloc[idx].tolist()]
        non_empty = sum(1 for value in row_values if value)
        score = non_empty
        if any("zone" in value for value in row_values):
            score += 10
        if any("branch" in value for value in row_values):
            score += 8
        if score > best_score:
            best_score = score
            best_index = idx
    return best_index


def _compose_headers(raw: pd.DataFrame, header_row_index: int) -> list[str]:
    headers: list[str] = []
    for col_idx in range(raw.shape[1]):
        values: list[str] = []
        for row_idx in range(header_row_index + 1):
            value = normalize_text(raw.iat[row_idx, col_idx])
            if value and value.lower() != "nan" and value not in values:
                values.append(value)
        headers.append(" ".join(values))
    return _contextualize_headers(_dedupe_headers(headers))


def _explicit_context(header: str) -> str | None:
    return _next_context(header, None)


def _should_prefix_with_context(header: str) -> bool:
    key = normalize_key(header)
    if not key or key.startswith("unnamed"):
        return False

    stable_headers = {
        "code",
        "branches",
        "zones",
        "branch head",
        "zonal head",
        "region",
        "level",
        "line ed",
    }
    if key in stable_headers:
        return False

    contextual_terms = [
        "ytd",
        "mthly",
        "monthly",
        "full yr",
        "full year",
        "bgt",
        "budget",
        "var",
        "variance",
        "high",
        "run rate",
        "cost to income",
        "loan to dep",
        "achvd",
        "achieved",
        "active",
        "inactive",
        "cards issued",
        "opened",
        "funded",
        "unfunded",
        "retrieved",
        "deployed",
        "reactivated",
    ]
    return _extract_period(header) is not None or any(term in key for term in contextual_terms)


def _contextualize_headers(headers: list[str]) -> list[str]:
    contextualized: list[str] = []
    current_context: str | None = None

    for header in headers:
        explicit = _explicit_context(header)
        if explicit is not None:
            current_context = explicit
            header_key = normalize_key(header)
            if explicit not in header_key:
                contextualized.append(f"{explicit.upper()} {header}")
            else:
                contextualized.append(header)
            continue

        if current_context and _should_prefix_with_context(header):
            contextualized.append(f"{current_context.upper()} {header}")
        else:
            contextualized.append(header)

    return contextualized


def _fallback_dataframe(path: str | Path) -> tuple[pd.DataFrame, int, str]:
    path_str = str(path)
    logger.info("[Parser] Step 1/4: Reading uploaded report body from '%s' (skip first 5 rows).", path_str)
    if path_str.lower().endswith(".csv"):
        uploaded = pd.read_csv(path_str, skiprows=5, header=None)
    else:
        uploaded = pd.read_excel(path_str, skiprows=5, header=None)
    logger.info(
        "[Parser] Loaded uploaded report body. Rows=%s, Columns=%s.",
        uploaded.shape[0],
        uploaded.shape[1],
    )
    logger.info(
        "[Parser] Step 2/4: Selecting structure template for %s uploaded columns.",
        uploaded.shape[1],
    )
    structure_path, structure_headers = _select_structure_template(uploaded.shape[1])

    if len(structure_headers) != uploaded.shape[1]:
        raise ValueError("Column count mismatch between uploaded file and available structure templates.")

    dataframe = pd.DataFrame(data=uploaded.values, columns=structure_headers)
    dataframe.columns = [normalize_text(column) for column in dataframe.columns]
    logger.info(
        "[Parser] Step 3/4: Applied structure headers from '%s'. Header count=%s. Data rows=%s.",
        structure_path,
        len(structure_headers),
        dataframe.shape[0],
    )
    return dataframe, 5, str(structure_path)


def _extract_period(value: object) -> tuple[int, int] | None:
    text = normalize_text(value)
    if not text:
        return None

    date_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
    if date_match:
        return int(date_match.group(1)), int(date_match.group(2))

    month_match = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[' -]?(\d{2,4})\b",
        text,
        re.IGNORECASE,
    )
    if not month_match:
        return None

    month_value = MONTH_NAME_TO_NUMBER[month_match.group(1).lower()]
    year_text = month_match.group(2)
    year_value = int(year_text)
    if year_value < 100:
        year_value += 2000
    return year_value, month_value


def _period_label(period: tuple[int, int]) -> str:
    year, month = period
    return datetime(year, month, 1).strftime("%b-%y")


def _sorted_unique_periods(columns: list[str]) -> list[tuple[int, int]]:
    ordered = list(dict.fromkeys(period for column in columns if (period := _extract_period(column))))
    return sorted(ordered)


def _resolve_static_mappings(columns: list[str]) -> dict[str, str]:
    normalized_columns = {column: normalize_key(column) for column in columns}
    mapping: dict[str, str] = {}
    for legacy_name, patterns in LEGACY_PATTERNS.items():
        for column, key in normalized_columns.items():
            if any(re.search(pattern, key) for pattern in patterns):
                mapping[legacy_name] = column
                break
    return mapping


def _reference_structure_paths() -> list[Path]:
    base = Path(settings.fallback_structure_path).resolve().parent
    candidates = sorted(base.glob("mpaStructure*.xlsx"))
    fallback = Path(settings.fallback_structure_path).resolve()
    if fallback in candidates:
        candidates.remove(fallback)
    if fallback.exists():
        candidates.insert(0, fallback)
    return candidates


def _select_structure_template(uploaded_column_count: int) -> tuple[Path, list[str]]:
    fallback = Path(settings.fallback_structure_path).resolve()
    if not fallback.exists():
        raise ValueError("No active structure template is available.")

    headers = _load_template_headers(fallback)
    logger.info(
        "[Parser] Active structure candidate: '%s' with %s headers.",
        fallback,
        len(headers),
    )
    if len(headers) != uploaded_column_count:
        logger.error(
            "[Parser] Active structure column mismatch. Active structure='%s' has %s headers but uploaded report has %s columns.",
            fallback,
            len(headers),
            uploaded_column_count,
        )
        raise ValueError("Column count mismatch between uploaded file and the active structure template.")

    logger.info(
        "[Parser] Active structure selected: '%s' with %s headers.",
        fallback,
        len(headers),
    )
    return fallback, headers


def _signature_header(value: object) -> str:
    key = normalize_key(value)
    key = re.sub(r"^\d+(?:\.\d+)?\s+", "", key)
    key = re.sub(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{2,4}\b",
        "period",
        key,
    )
    key = re.sub(r"\b20\d{2}\s+\d{2}\s+\d{2}(?:\s+\d{2}){3}\b", "period", key)
    key = re.sub(r"\b\d+(?:\.\d+)?\b", "", key)
    key = re.sub(r"\blevel \b", "level ", key)
    return re.sub(r"\s+", " ", key).strip()


def _next_context(header: str, current_context: str | None) -> str | None:
    key = normalize_key(header)
    context_rules = [
        ("pbt", [r"\bpbt\b"]),
        ("dda", [r"\bdda\b"]),
        ("sav", [r"\bsav\b", r"\bsavings\b"]),
        ("fd", [r"\bfd\b", r"\bfixed deposit\b"]),
        ("dp", [r"\bdp\b", r"\btotal deposits\b", r"\bdomiciliary deposits\b"]),
        ("tra", [r"\btra\b", r"\bretail loans\b", r"\brisk assets\b", r"\bloan to dep\b"]),
        ("ab", [r"\bab\b", r"\bagency banking\b"]),
        ("ao", [r"\baccounts opened\b", r"\bc a opened\b", r"\bs a opened\b"]),
        ("cds1", [r"\bcards august\b"]),
        ("cds2", [r"\bcards september\b"]),
        ("ce", [r"\bce\b", r"\bchannels enrollment\b"]),
        ("aob", [r"\baob\b", r"\bagents onboarded\b"]),
        ("nxp", [r"\bnxp\b"]),
        ("dmt act", [r"\bdormant account\b", r"\bdmt\b.*\bact\b"]),
        ("pos", [r"\bpos terminal\b", r"\bactive pos\b", r"\bpos\b"]),
    ]
    for context, patterns in context_rules:
        if any(re.search(pattern, key) for pattern in patterns):
            return context
    return current_context


def _signature_sequence(headers: list[str]) -> list[str]:
    sequence: list[str] = []
    current_context: str | None = None
    for header in headers:
        current_context = _next_context(header, current_context)
        key = _signature_header(header)
        if not key:
            sequence.append("blank")
            continue

        contextual_terms = {
            "period",
            "mom variance",
            "ytd variance",
            "12 month high",
            "24 month high",
            "full yr bgt",
            "full year bgt",
            "run rate",
            "var",
        }
        if current_context and any(term in key for term in contextual_terms):
            sequence.append(f"{current_context} {key}".strip())
        elif current_context and key == "unnamed":
            sequence.append(f"{current_context} blank")
        else:
            sequence.append(key)
    return sequence


def _load_template_headers(path: Path) -> list[str]:
    return [normalize_text(header) for header in pd.read_excel(path, nrows=0).columns.tolist()]


def _aligned_template_mapping(upload_headers: list[str]) -> dict[str, str]:
    upload_signature = _signature_sequence(upload_headers)
    best_score = 0.0
    best_mapping: dict[str, str] = {}

    for template_path in _reference_structure_paths():
        template_headers = _load_template_headers(template_path)
        template_signature = _signature_sequence(template_headers)
        matcher = SequenceMatcher(a=template_signature, b=upload_signature)
        score = matcher.ratio()
        if score <= best_score:
            continue

        candidate_mapping: dict[str, str] = {}
        for block in matcher.get_matching_blocks():
            if block.size == 0:
                continue
            for offset in range(block.size):
                template_header = template_headers[block.a + offset]
                upload_header = upload_headers[block.b + offset]
                candidate_mapping.setdefault(template_header, upload_header)

        if candidate_mapping:
            best_score = score
            best_mapping = candidate_mapping

    return best_mapping


def _family_matches(column: str, family: str) -> bool:
    return re.search(rf"\b{family.lower()}\b", normalize_key(column)) is not None


def _is_monthly_value_column(column: str, family: str) -> bool:
    key = normalize_key(column)
    if not _family_matches(column, family):
        return False
    if _extract_period(column) is None:
        return False
    blocked_terms = [
        "bgt",
        "budget",
        "variance",
        "var",
        "high",
        "loan to dep",
        "reactivated",
        "active",
        "inactive",
        "issued",
        "opened",
        "retrieved",
        "deployed",
        "total",
        "value",
        "volume",
    ]
    return not any(term in key for term in blocked_terms)


def _resolve_dynamic_period_mappings(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}

    for family, slots in DYNAMIC_FAMILY_SLOTS.items():
        period_columns = [
            (column, _extract_period(column))
            for column in columns
            if _is_monthly_value_column(column, family)
        ]
        ordered = sorted(
            [(column, period) for column, period in period_columns if period is not None],
            key=lambda item: item[1],
        )
        selected = ordered[-len(slots) :]
        if len(selected) == len(slots):
            for slot_name, (column, _) in zip(slots, selected):
                mapping[slot_name] = column

    ab_period_columns = [
        (column, _extract_period(column))
        for column in columns
        if _family_matches(column, "AB") and _extract_period(column) is not None and "var" not in normalize_key(column)
    ]
    ab_ordered = sorted(
        [(column, period) for column, period in ab_period_columns if period is not None],
        key=lambda item: item[1],
    )
    selected_ab = ab_ordered[-len(AB_SLOTS) :]
    if len(selected_ab) == len(AB_SLOTS):
        for slot_name, (column, _) in zip(AB_SLOTS, selected_ab):
            mapping[slot_name] = column

    return mapping


def _apply_canonical_mapping(dataframe: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    renamed = dataframe.rename(columns={raw_name: canonical for canonical, raw_name in mapping.items()}).copy()
    return renamed.loc[:, ~renamed.columns.duplicated()]


def _extract_zones(dataframe: pd.DataFrame) -> list[str]:
    if "ZONES" not in dataframe.columns:
        return []
    return sorted(
        {
            cleaned
            for value in dataframe["ZONES"].tolist()
            if (cleaned := normalize_text(value)) and normalize_key(cleaned) != "zones"
        }
    )


def _detected_period_label(columns: list[str]) -> str | None:
    periods = _sorted_unique_periods(columns)
    if not periods:
        return None
    active_window = periods[-3:]
    if len(active_window) == 1:
        return _period_label(active_window[0])
    return f"{_period_label(active_window[0])} to {_period_label(active_window[-1])}"


def _normalize_dataframe_values(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in normalized.columns:
        if column in {"ZONES", "BRANCHES"}:
            normalized[column] = normalized[column].map(normalize_text)
        else:
            normalized[column] = normalized[column].map(parse_numeric)
    return normalized


def _parse_dynamic_workbook(path: str) -> tuple[pd.DataFrame, int, list[str], dict[str, str]]:
    raw = _read_raw_table(path)
    header_row_index = _detect_header_row(raw)
    headers = _compose_headers(raw, header_row_index)
    dataframe = raw.iloc[header_row_index + 1 :].reset_index(drop=True).copy()
    dataframe.columns = headers
    dataframe = dataframe.dropna(how="all")
    mapping = _aligned_template_mapping(list(dataframe.columns))
    for canonical, raw_name in _resolve_static_mappings(list(dataframe.columns)).items():
        mapping.setdefault(canonical, raw_name)
    for canonical, raw_name in _resolve_dynamic_period_mappings(list(dataframe.columns)).items():
        mapping.setdefault(canonical, raw_name)
    renamed = _apply_canonical_mapping(dataframe, mapping)
    return renamed, header_row_index, headers, mapping


def _parse_structure_workbook(path: str) -> tuple[pd.DataFrame, int, list[str], dict[str, str], str]:
    dataframe, header_row_index, structure_source_path = _fallback_dataframe(path)
    headers = list(dataframe.columns)
    mapping = {column: column for column in dataframe.columns}
    return dataframe.copy(), header_row_index, headers, mapping, structure_source_path


def parse_uploaded_workbook(path: str) -> ParsedWorkbook:
    logger.info("[Parser] Starting manual structure parse for '%s'.", path)
    structure_frame, structure_header_index, structure_headers, structure_mapping, structure_source_path = _parse_structure_workbook(path)
    chosen_frame = _normalize_dataframe_values(structure_frame)
    chosen_header_index = structure_header_index
    chosen_headers = structure_headers
    chosen_mapping = structure_mapping
    missing_fields = [field for field in REQUIRED_FIELDS if field not in chosen_frame.columns]
    zones = _extract_zones(chosen_frame)
    logger.info(
        "[Parser] Step 4/4: Parse complete. Structure='%s', header row index=%s, missing required fields=%s, zones found=%s.",
        structure_source_path,
        chosen_header_index,
        missing_fields,
        len(zones),
    )

    return ParsedWorkbook(
        dataframe=chosen_frame,
        header_row_index=chosen_header_index,
        mapped_fields=chosen_mapping,
        missing_fields=missing_fields,
        detected_period_label=_detected_period_label(chosen_headers),
        zones=zones,
        structure_source_path=structure_source_path,
    )
