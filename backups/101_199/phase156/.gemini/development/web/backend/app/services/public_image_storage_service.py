import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class StoredImage:
    file_path: str
    provider_key: Optional[str] = None
    storage: str = "local"


class PublicImageStorageService:
    LOCAL_UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "app" / "static" / "uploads"

    @classmethod
    def upload_message_template_image(cls, filename: str, file_content: bytes, content_type: str, folder: str = "message_templates") -> StoredImage:
        if cls._cloudinary_enabled():
            return cls._upload_to_cloudinary(filename=filename, file_content=file_content, content_type=content_type, folder=folder)
        return cls._save_locally(filename=filename, file_content=file_content, folder=folder)

    @classmethod
    def delete_image(cls, file_path: Optional[str], provider_key: Optional[str] = None) -> bool:
        if provider_key and provider_key.startswith("cloudinary:"):
            return cls._delete_from_cloudinary(provider_key.removeprefix("cloudinary:"))
        return cls._delete_local(file_path)

    @staticmethod
    def _cloudinary_enabled() -> bool:
        return bool(os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()) and (
            bool(os.getenv("CLOUDINARY_UNSIGNED_UPLOAD_PRESET", "").strip())
            or (
                bool(os.getenv("CLOUDINARY_API_KEY", "").strip())
                and bool(os.getenv("CLOUDINARY_API_SECRET", "").strip())
            )
        )

    @staticmethod
    def _build_multipart_body(fields: dict[str, str], file_field: str, filename: str, file_content: bytes, content_type: str) -> tuple[bytes, str]:
        boundary = f"----D4Boundary{uuid.uuid4().hex}"
        lines: list[bytes] = []
        for key, value in fields.items():
            lines.extend(
                [
                    f"--{boundary}".encode(),
                    f'Content-Disposition: form-data; name="{key}"'.encode(),
                    b"",
                    str(value).encode(),
                ]
            )
        lines.extend(
            [
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode(),
                f"Content-Type: {content_type}".encode(),
                b"",
                file_content,
                f"--{boundary}--".encode(),
                b"",
            ]
        )
        return b"\r\n".join(lines), boundary

    @staticmethod
    def _sign_params(params: dict[str, str], api_secret: str) -> str:
        payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
        return hashlib.sha1(f"{payload}{api_secret}".encode()).hexdigest()

    @classmethod
    def _upload_to_cloudinary(cls, filename: str, file_content: bytes, content_type: str, folder: str) -> StoredImage:
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
        upload_preset = os.getenv("CLOUDINARY_UNSIGNED_UPLOAD_PRESET", "").strip()
        api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
        api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
        public_id = f"{Path(filename).stem}-{uuid.uuid4().hex[:10]}"

        fields = {"folder": folder, "public_id": public_id}
        if upload_preset:
            fields["upload_preset"] = upload_preset
        else:
            timestamp = str(int(time.time()))
            signature_params = {"folder": folder, "public_id": public_id, "timestamp": timestamp}
            fields.update(
                {
                    "timestamp": timestamp,
                    "api_key": api_key,
                    "signature": cls._sign_params(signature_params, api_secret),
                }
            )

        body, boundary = cls._build_multipart_body(
            fields=fields,
            file_field="file",
            filename=filename,
            file_content=file_content,
            content_type=content_type,
        )
        request = urllib.request.Request(
            url=f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="ignore")
            logger.error("Cloudinary upload failed: %s", detail or exc.reason)
            raise ValueError("Cloudinary upload failed.") from exc

        secure_url = payload.get("secure_url")
        remote_public_id = payload.get("public_id")
        if not secure_url or not remote_public_id:
            raise ValueError("Cloudinary upload response was incomplete.")
        return StoredImage(file_path=secure_url, provider_key=f"cloudinary:{remote_public_id}", storage="cloudinary")

    @classmethod
    def _save_locally(cls, filename: str, file_content: bytes, folder: str) -> StoredImage:
        extension = Path(filename).suffix or ".jpg"
        local_filename = f"{uuid.uuid4()}{extension}"
        upload_dir = cls.LOCAL_UPLOAD_ROOT / folder
        upload_dir.mkdir(parents=True, exist_ok=True)
        local_path = upload_dir / local_filename
        local_path.write_bytes(file_content)
        return StoredImage(file_path=f"/static/uploads/{folder}/{local_filename}", provider_key="", storage="local")

    @classmethod
    def _delete_from_cloudinary(cls, public_id: str) -> bool:
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
        api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
        api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
        if not cloud_name or not api_key or not api_secret:
            logger.warning("Skipping Cloudinary delete because signed credentials are missing.")
            return False

        timestamp = str(int(time.time()))
        body = urllib.parse.urlencode(
            {
                "public_id": public_id,
                "timestamp": timestamp,
                "api_key": api_key,
                "signature": cls._sign_params({"public_id": public_id, "timestamp": timestamp}, api_secret),
            }
        ).encode()
        request = urllib.request.Request(
            url=f"https://api.cloudinary.com/v1_1/{cloud_name}/image/destroy",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="ignore")
            logger.warning("Cloudinary delete failed: %s", detail or exc.reason)
            return False
        return payload.get("result") in {"ok", "not found"}

    @classmethod
    def _delete_local(cls, file_path: Optional[str]) -> bool:
        if not file_path or not file_path.startswith("/static/uploads/"):
            return False
        local_file = cls.LOCAL_UPLOAD_ROOT / file_path.removeprefix("/static/uploads/")
        if not local_file.exists():
            return False
        try:
            local_file.unlink()
            return True
        except OSError:
            logger.warning("Failed to remove local uploaded image: %s", local_file)
            return False
