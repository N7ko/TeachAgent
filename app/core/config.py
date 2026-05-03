import os


class Settings:
    app_name = "TeachAgent API"
    version = "0.1.0"
    environment = os.getenv("APP_ENV", "local")
    cors_origins = os.getenv("CORS_ORIGINS", "*")

    @property
    def cors_allow_origins(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return self.cors_allow_origins != ["*"]


settings = Settings()

