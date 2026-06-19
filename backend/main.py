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
    def val_filename(cls, v):
        ext = v.rsplit(".", 1)[-1].lower() if "." in v else ""
        if ext not in ALLOWED_EXT:
            raise ValueError(f"Extension no permitida: {ext}")
        return v

    @field_validator("content_type")
    @classmethod
    def val_content_type(cls, v):
        if v.lower() not in ALLOWED_TYPES:
            raise ValueError(f"Tipo no permitido: {v}")
        return v.lower()

    @field_validator("sha256")
    @classmethod
    def val_sha256(cls, v):
        if v and len(v) not in (0, 64):
            raise ValueError("sha256 debe ser cadena hexadecimal de 64 chars")
        return v.lower() if v else v

    @field_validator("file_size")
    @classmethod
    def val_size(cls, v):
        if v > MAX_BYTES:
            raise ValueError("Archivo mayor a 20 MB")
        return v

class PresignedUrlResponse(BaseModel):
    url: str
    method: str = "PUT"
    key: str

# construye el cliente s3 con las credenciales del .env
def get_s3_client():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"]     = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.client("s3", **kwargs)

app = FastAPI(title="ArchivaCloud API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

