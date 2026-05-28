from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    generator_model: str


settings = Settings(generator_model="gemma4:e2b-mlx")
