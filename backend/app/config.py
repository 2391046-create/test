from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/livingfund"
    XRPL_TESTNET_URL: str = "https://s.altnet.rippletest.net:51234"
    ENCRYPTION_KEY: str = ""
    XRPL_ISSUER_ADDRESS: str = ""
    XRPL_ISSUER_SEED: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
