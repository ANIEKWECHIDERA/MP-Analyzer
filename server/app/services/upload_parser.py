from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import pandas as pd

from ..config import settings
from .normalization import normalize_key, normalize_text, parse_numeric


LEGACY_PATTERNS: dict[str, list[str]] = {
    "ZONES": [r"\bzones?\b"],
    "BRANCHES": [r"\bbranches?\b"],
    "PBT 2025 YTD ACHVD": [r"\bpbt\b.*\bytd\b.*\bach"],
    "PBT 2025 FULL YR BGT": [r"\bpbt\b.*\bfull\b.*\byr\b.*\bbgt", r"\bpbt\b.*\bbudget\b"],
    "PBT 2025 YOY VAR": [r"\bpbt\b.*\byoy\b.*\bvar"],
    "PBT Exp Run Rate": [r"\bpbt\b.*\brun rate"],
    "PBT Cost to Income Ratio": [r"\bpbt\b.*\bcost to income"],
    "PBT Mthly Var": [r"\bpbt\b.*\b(?:mthly|monthly)\b.*\bvar"],
    "DDA May-25": [r"\bdda\b.*\bmay\b.*\b25\b"],
    "DDA Jun-25": [r"\bdda\b.*\bjun\b.*\b25\b"],
    "DDA Jul-25": [r"\bdda\b.*\bjul\b.*\b25\b"],
    "DDA 2025 FULL YR BGT": [r"\bdda\b.*\bfull\b.*\byr\b.*\bbgt"],
    "DDA YTD Variance": [r"\bdda\b.*\bytd\b.*\bvar"],
    "DDA MOM Variance": [r"\bdda\b.*\bmom\b.*\bvar"],
    "SAV May-25": [r"\bsav\b.*\bmay\b.*\b25\b"],
    "SAV Jun-25": [r"\bsav\b.*\bjun\b.*\b25\b"],
    "SAV Jul-25": [r"\bsav\b.*\bjul\b.*\b25\b"],
    "SAV 2025 FULL YR BGT": [r"\bsav\b.*\bfull\b.*\byr\b.*\bbgt"],
    "SAV YTD Variance": [r"\bsav\b.*\bytd\b.*\bvar"],
    "SAV MOM Variance": [r"\bsav\b.*\bmom\b.*\bvar"],
    "FD May-25": [r"\bfd\b.*\bmay\b.*\b25\b"],
    "FD Jun-25": [r"\bfd\b.*\bjun\b.*\b25\b"],
    "FD Jul-25": [r"\bfd\b.*\bjul\b.*\b25\b"],
    "FD 2025 FULL YR BGT": [r"\bfd\b.*\bfull\b.*\byr\b.*\bbgt"],
    "FD YTD Variance": [r"\bfd\b.*\bytd\b.*\bvar"],
    "FD MOM Variance": [r"\bfd\b.*\bmom\b.*\bvar"],
    "DP May-25": [r"\bdp\b.*\bmay\b.*\b25\b"],
    "DP Jun-25": [r"\bdp\b.*\bjun\b.*\b25\b"],
    "DP Jul-25": [r"\bdp\b.*\bjul\b.*\b25\b"],
    "DP 2025 FULL YR BGT": [r"\bdp\b.*\bfull\b.*\byr\b.*\bbgt"],
    "DP YTD Variance": [r"\bdp\b.*\bytd\b.*\bvar"],
    "TRA May-25": [r"\btra\b.*\bmay\b.*\b25\b"],
    "TRA Jun-25": [r"\btra\b.*\bjun\b.*\b25\b"],
    "TRA Jul-25": [r"\btra\b.*\bjul\b.*\b25\b"],
    "TRA Loan to Dep": [r"\btra\b.*\bloan to dep"],
    "TRA YTD Variance": [r"\btra\b.*\bytd\b.*\bvar"],
    "AB Jun-25": [r"\bab\b.*\bjun\b.*\b25\b"],
    "AB Jul-25": [r"\bab\b.*\bjul\b.*\b25\b"],
    "AB VAR": [r"\bab\b.*\bvar"],
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
    "CE May-25": [r"\bce\b.*\bmay\b.*\b25\b"],
    "CE Jun-25": [r"\bce\b.*\bjun\b.*\b25\b"],
    "CE Jul-25": [r"\bce\b.*\bjul\b.*\b25\b"],
    "AOB May-25": [r"\baob\b.*\bmay\b.*\b25\b"],
    "AOB Jun-25": [r"\baob\b.*\bjun\b.*\b25\b"],
    "AOB Jul-25": [r"\baob\b.*\bjul\b.*\b25\b"],
    "POS ACTIVE": [r"\bpos\b.*\bactive"],
    "POS INACTIVE": [r"\bpos\b.*\binactive"],
    "POS NEWLY DEPLOYED": [r"\bpos\b.*\bnewly deployed"],
    "POS RETRIEVED": [r"\bpos\b.*\bretrieved"],
    "NXP May-25": [r"\bnxp\b.*\bmay\b.*\b25\b"],
    "NXP Jun-25": [r"\bnxp\b.*\bjun\b.*\b25\b"],
    "NXP Jul-25": [r"\bnxp\b.*\bjul\b.*\b25\b"],
    "NXP YOY VAR": [r"\bnxp\b.*\byoy\b.*\bvar"],
    "TOTAL_DMT_ACT": [r"\btotal\b.*\bdmt\b.*\bact"],
    "No. Reactivated DMT_ACT": [r"\breactivated\b.*\bdmt\b.*\bact"],
    "% Reactivated DMT_ACT": [r"\bpercent\b.*\breactivated\b.*\bdmt\b.*\bact"],
}

REQUIRED_FIELDS = ["ZONES", "BRANCHES", "PBT 2025 YTD ACHVD", "DDA Jul-25", "SAV Jul-25", "FD Jul-25", "DP Jul-25"]


@dataclass
class ParsedWorkbook:
    dataframe: pd.DataFrame
    header_row_index: int
    mapped_fields: dict[str, str]
    missing_fields: list[str]
    detected_period_label: str | None
    zones: list[str]


def _read_raw_table(path: str) -> pd.DataFrame:
    if path.lower().endswith(".csv"):
        return pd.read_csv(path, header=None, dtype=str)
    return pd.read_excel(path, header=None, dtype=str)


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
    return _dedupe_headers(headers)


def _fallback_dataframe(path: str) -> tuple[pd.DataFrame, int]:
    structure_headers = pd.read_excel(settings.fallback_structure_path, nrows=0).columns.tolist()
    if path.lower().endswith(".csv"):
        uploaded = pd.read_csv(path, skiprows=5, header=None)
    else:
        uploaded = pd.read_excel(path, skiprows=5, header=None)
    if len(structure_headers) != uploaded.shape[1]:
        raise ValueError(
            "Column count mismatch between uploaded file and structure template."
        )
    dataframe = pd.DataFrame(data=uploaded.values, columns=structure_headers)
    dataframe.columns = [normalize_text(column) for column in dataframe.columns]
    return dataframe, 5


def _resolve_mappings(columns: list[str]) -> dict[str, str]:
    normalized_columns = {column: normalize_key(column) for column in columns}
    mapping: dict[str, str] = {}
    for legacy_name, patterns in LEGACY_PATTERNS.items():
        for column, key in normalized_columns.items():
            if any(re.search(pattern, key) for pattern in patterns):
                mapping[legacy_name] = column
                break
    return mapping


def _extract_zones(dataframe: pd.DataFrame) -> list[str]:
    if "ZONES" not in dataframe.columns:
        return []
    return sorted(
        {
            cleaned
            for value in dataframe["ZONES"].tolist()
            if (cleaned := normalize_text(value))
            and normalize_key(cleaned) != "zones"
        }
    )


def _detected_period_label(columns: list[str]) -> str | None:
    matches: list[str] = []
    for column in columns:
        match = re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[- ]\d{2}\b", normalize_key(column))
        if match:
            matches.append(match.group(0).title().replace(" ", "-"))
    ordered = list(dict.fromkeys(matches))
    if not ordered:
        return None
    return ordered[0] if len(ordered) == 1 else f"{ordered[0]} to {ordered[-1]}"


def parse_uploaded_workbook(path: str) -> ParsedWorkbook:
    try:
        dataframe, header_row_index = _fallback_dataframe(path)
        headers = list(dataframe.columns)
        mapping = {column: column for column in dataframe.columns}
    except ValueError:
        raw = _read_raw_table(path)
        header_row_index = _detect_header_row(raw)
        headers = _compose_headers(raw, header_row_index)
        dataframe = raw.iloc[header_row_index + 1 :].reset_index(drop=True).copy()
        dataframe.columns = headers
        dataframe = dataframe.dropna(how="all")
        mapping = _resolve_mappings(list(dataframe.columns))
        renamed = dataframe.rename(
            columns={raw_name: canonical for canonical, raw_name in mapping.items()}
        ).copy()
    else:
        renamed = dataframe.copy()

    for column in renamed.columns:
        if column in {"ZONES", "BRANCHES"}:
            renamed[column] = renamed[column].map(normalize_text)
        else:
            renamed[column] = renamed[column].map(parse_numeric)

    missing_fields = [field for field in REQUIRED_FIELDS if field not in renamed.columns]
    return ParsedWorkbook(
        dataframe=renamed,
        header_row_index=header_row_index,
        mapped_fields=mapping,
        missing_fields=missing_fields,
        detected_period_label=_detected_period_label(headers),
        zones=_extract_zones(renamed),
    )
