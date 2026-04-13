from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://postgres:YOUR_SUPABASE_PASSWORD@"
        "YOUR_SUPABASE_HOST:6543/postgres"
    )
    cors_origins: str = "*"
    template_path: str = str(BASE_DIR / "mpatemplate.docx")
    fallback_structure_path: str = str(BASE_DIR / "mpaStructure.xlsx")
    schema_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        normalized = str(value).strip().strip("\"'").strip()
        if normalized.startswith("postgresql://"):
            normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)

        parsed = urlsplit(normalized)
        filtered_query = [
            (key, query_value)
            for key, query_value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in {"pgbouncer", "connection_limit"}
        ]
        if filtered_query != parse_qsl(parsed.query, keep_blank_values=True):
            normalized = urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    urlencode(filtered_query),
                    parsed.fragment,
                )
            )
        return normalized

    @field_validator("template_path", "fallback_structure_path", mode="before")
    @classmethod
    def resolve_relative_paths(cls, value: str) -> str:
        candidate = Path(str(value).strip().strip("\"'"))
        if candidate.is_absolute():
            return str(candidate)
        return str((BASE_DIR / candidate).resolve())


settings = Settings()
