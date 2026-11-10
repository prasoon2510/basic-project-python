from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Ecommerce Management API"

    DATABASE_URL: str

    ZITADEL_ISSUER: str
    ZITADEL_API_AUDIENCE: str
    ZITADEL_JWKS_URL: str
    ZITADEL_CLIENT_ID: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()  # pyright: ignore[reportCallIssue]