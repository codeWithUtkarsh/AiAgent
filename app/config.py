from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        env="ANTHROPIC_MODEL"
    )

    # GitHub Configuration
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")

    # Application Configuration
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    workspace_dir: str = Field(default="./workspace", env="WORKSPACE_DIR")

    # Repository Configuration
    default_branch_prefix: str = Field(
        default="dependency-updates",
        env="DEFAULT_BRANCH_PREFIX"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()
