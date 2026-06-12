import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    allowed_origins: list[str] = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    )

    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "10"))
    )
    input_cost_per_1k_tokens: float = field(
        default_factory=lambda: float(os.getenv("INPUT_COST_PER_1K_TOKENS", "0.00015"))
    )
    output_cost_per_1k_tokens: float = field(
        default_factory=lambda: float(os.getenv("OUTPUT_COST_PER_1K_TOKENS", "0.0006"))
    )
    estimated_output_tokens: int = field(
        default_factory=lambda: int(os.getenv("ESTIMATED_OUTPUT_TOKENS", "100"))
    )
    history_max_messages: int = field(
        default_factory=lambda: int(os.getenv("HISTORY_MAX_MESSAGES", "20"))
    )
    history_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("HISTORY_TTL_SECONDS", "86400"))
    )

    def validate(self):
        if not self.agent_api_key:
            raise ValueError("AGENT_API_KEY must be set")
        return self


settings = Settings().validate()
