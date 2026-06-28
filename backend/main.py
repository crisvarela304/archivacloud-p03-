import boto3
import logging
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    aws_region: str = "us-west-2"
    aws_s3_bucket: str = "archivacloud-p03"
    presigned_url_expiration: int = 3600


settings = Settings()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("archivacloud")

ALLOWED_EXT = {"mp3", "wav"}
ALLOWED_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/wave"}
MAX_BYTES = 20 * 1024 * 1024


class PresignedUrlRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    file_size: int = Field(..., gt=0)
    sha256: str = Field(default="", max_length=64)

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
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
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


@app.get("/healthz")
def health():
    return {"status": "healthy"}


@app.post("/api/upload/presigned-url", response_model=PresignedUrlResponse)
def generate_presigned_url(body: PresignedUrlRequest):
    s3 = get_s3_client()
    key = body.filename
    params: dict[str, Any] = {
        "Bucket": settings.aws_s3_bucket, "Key": key,
        "ContentType": body.content_type,
    }
    if body.sha256:
        params["Metadata"] = {"sha256": body.sha256}
    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object", Params=params,
            ExpiresIn=settings.presigned_url_expiration, HttpMethod="PUT",
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.error("Error presigned URL: %s", code)
        raise HTTPException(status_code=502, detail=f"Error S3: {code}")
    return PresignedUrlResponse(url=url, key=key)


class DynamoDBItem(BaseModel):
    id_tabla: str
    nombre_proyecto: str
    descripcion: str


@app.post("/api/files/metadata", status_code=201)
def save_metadata(item: DynamoDBItem):
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token
        )
        table = dynamodb.Table('database_dynamo')
        table.put_item(
            Item={
                'id_tabla': item.id_tabla,
                'nombre_proyecto': item.nombre_proyecto,
                'descripcion': item.descripcion
            }
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.error("Error DynamoDB: %s", code)
        raise HTTPException(status_code=502, detail=f"Error DynamoDB: {code}")
    return {"message": "Metadata guardada en DynamoDB"}


class FileItem(BaseModel):
    key: str
    filename: str
    size_bytes: int
    last_modified: str
    sha256: str = ""
    download_url: str = ""


@app.get("/api/files", response_model=list[FileItem])
def list_files():
    s3 = get_s3_client()
    try:
        resp = s3.list_objects_v2(Bucket=settings.aws_s3_bucket)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        raise HTTPException(status_code=502, detail=f"Error S3: {code}")
    items = []
    for obj in resp.get("Contents", []):
        key = obj["Key"]
        meta = {}
        try:
            head = s3.head_object(Bucket=settings.aws_s3_bucket, Key=key)
            meta = head.get("Metadata", {})
        except ClientError:
            pass
        dl_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.aws_s3_bucket,
                "Key": key},
            ExpiresIn=3600)
        items.append(FileItem(
            key=key, filename=key, size_bytes=obj["Size"],
            last_modified=obj["LastModified"].isoformat(),
            sha256=meta.get("sha256", ""), download_url=dl_url,
        ))
    return items


@app.delete("/api/files/{key:path}", status_code=204)
def delete_file(key: str):
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=settings.aws_s3_bucket, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.error("Error DELETE: %s", code)
        raise HTTPException(status_code=502, detail=f"Error S3: {code}")
