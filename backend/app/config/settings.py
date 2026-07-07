import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_path: str = "societas.db"
    cors_origins: str = "*"
    log_level: str = "INFO"
    simulation_population_size: int = 100
    simulation_seed: int | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_path=os.environ.get("SOCIETAS_DATABASE_PATH", "societas.db"),
            cors_origins=os.environ.get("SOCIETAS_CORS_ORIGINS", "*"),
            log_level=os.environ.get("SOCIETAS_LOG_LEVEL", "INFO"),
            simulation_population_size=int(os.environ.get("SOCIETAS_SIMULATION_POPULATION_SIZE", "100")),
            simulation_seed=_parse_int_or_none(os.environ.get("SOCIETAS_SIMULATION_SEED")),
        )


def _parse_int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
