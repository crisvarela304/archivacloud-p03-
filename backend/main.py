import boto3
import logging
import urllib.parse
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    aws_region: str = "us-west-2"
    aws_s3_bucket: str = "archivacloud-p03"
    presigned_url_expiration: int = 3600

settings = Settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("archivacloud")

ALLOWED_EXT   = {"mp3", "wav"}
ALLOWED_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/wave"}
MAX_BYTES     = 20 * 1024 * 1024

class PresignedUrlRequest(BaseModel):
    filename:     str = Field(..., min_length=1, max_length=255)
    content_type: str
    file_size:    int = Field(..., gt=0)
    sha256:       str = Field(default="", max_length=64)

    @field_validator("filename")
    @classmethod
