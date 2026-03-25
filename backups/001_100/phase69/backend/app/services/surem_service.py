import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.models import ServiceToken

logger = logging.getLogger(__name__)


class SureMService:
    TOKEN_SERVICE_NAME = "surem"
    IMAGE_CACHE_PREFIX = "surem_image:"
    TOKEN_REFRESH_MARGIN = timedelta(minutes=5)
    IMAGE_REFRESH_MARGIN = timedelta(hours=1)
    TOKEN_LOCK_ID = 43120419

    @staticmethod
    def _broker_base_url() -> str:
        return os.getenv("SUREM_BROKER_URL", "").strip().rstrip("/")

    @staticmethod
    def _broker_enabled() -> bool:
        return bool(SureMService._broker_base_url())

    @staticmethod
    def _broker_headers() -> Dict[str, str]:
        headers: Dict[str, str] = {}
        secret = os.getenv("SUREM_BROKER_SECRET", "").strip()
        if secret:
            headers["X-Broker-Secret"] = secret
        return headers

    @staticmethod
    def _broker_request(method: str, path: str, json_body: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        base_url = SureMService._broker_base_url()
        if not base_url:
            return {"status": "error", "message": "SUREM_BROKER_URL is not configured."}

        url = f"{base_url}{path}"
        try:
            response = requests.request(
                method,
                url,
                headers=SureMService._broker_headers(),
                json=json_body,
                files=files,
                timeout=30,
            )
            data = response.json()
            if response.status_code >= 400:
                if isinstance(data, dict):
                    data.setdefault("status", "error")
                    return data
                return {"status": "error", "message": str(data)}
            return data if isinstance(data, dict) else {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"SureM broker request failed: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _supports_advisory_lock(db: Session) -> bool:
        bind = db.get_bind()
        return bind is not None and bind.dialect.name == "postgresql"

    @staticmethod
    def _acquire_lock(db: Session) -> None:
        if SureMService._supports_advisory_lock(db):
            db.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": SureMService.TOKEN_LOCK_ID})

    @staticmethod
    def _release_lock(db: Session) -> None:
        if SureMService._supports_advisory_lock(db):
            db.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": SureMService.TOKEN_LOCK_ID})

    @staticmethod
    def _normalize_expires_at(expires_at: Optional[datetime]) -> Optional[datetime]:
        if expires_at is None:
            return None
        if expires_at.tzinfo is None:
            return expires_at.replace(tzinfo=timezone.utc)
        return expires_at.astimezone(timezone.utc)

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        return SureMService._normalize_expires_at(datetime.fromisoformat(normalized))

    @staticmethod
    def _token_is_valid(access_token: Optional[str], expires_at: Optional[datetime], margin: timedelta) -> bool:
        normalized_expires_at = SureMService._normalize_expires_at(expires_at)
        if not access_token or normalized_expires_at is None:
            return False
        return datetime.now(timezone.utc) < normalized_expires_at - margin

    @staticmethod
    def _upsert_secret(db: Session, service_name: str, access_token: str, expires_at: Optional[datetime]) -> None:
        row = db.query(ServiceToken).filter(ServiceToken.service_name == service_name).first()
        if row is None:
            row = ServiceToken(service_name=service_name)
            db.add(row)
        row.access_token = access_token
        row.expires_at = SureMService._normalize_expires_at(expires_at)

    @staticmethod
    def _request_new_access_token() -> Tuple[Optional[str], Optional[datetime], Dict[str, Any]]:
        user_code = os.getenv("SUREM_USER_CODE")
        secret_key = os.getenv("SUREM_SECRET_KEY")
        auth_url = os.getenv("SUREM_AUTH_URL")
        diagnostics: Dict[str, Any] = {
            "auth_url_present": bool(auth_url),
            "user_code_present": bool(user_code),
            "secret_key_present": bool(secret_key),
        }

        if not all([user_code, secret_key, auth_url]):
            logger.error("SureM credentials missing in environment variables.")
            diagnostics["error"] = "missing_credentials"
            return None, None, diagnostics

        logger.info("Fetching new SureM access token.")
        try:
            response = requests.post(
                str(auth_url),
                headers={"Content-Type": "application/json"},
                json={"userCode": user_code, "secretKey": secret_key},
                timeout=10,
            )
            if response.status_code != 200:
                logger.error(f"SureM Auth HTTP Error: {response.status_code} - {response.text}")
                diagnostics["error"] = "auth_http_error"
                diagnostics["status_code"] = response.status_code
                diagnostics["response_text"] = response.text[:300]
                return None, None, diagnostics

            data = response.json()
            if data.get("code") != "A0000":
                logger.error(f"SureM Auth Error: Code {data.get('code')}, {data}")
                diagnostics["error"] = "auth_code_error"
                diagnostics["code"] = data.get("code")
                diagnostics["message"] = data.get("message")
                return None, None, diagnostics

            new_token = data.get("data", {}).get("accessToken")
            expires_in_seconds = data.get("data", {}).get("expiresIn", 3600)
            if not new_token:
                logger.error(f"SureM Auth response missing accessToken: {data}")
                diagnostics["error"] = "missing_access_token"
                return None, None, diagnostics

            new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
            logger.info(f"Successfully refreshed SureM token. Expires at: {new_expires_at.isoformat()}")
            diagnostics["source"] = "fresh_auth"
            diagnostics["expires_at"] = new_expires_at.isoformat()
            return new_token, new_expires_at, diagnostics
        except Exception as e:
            logger.error(f"Failed to fetch SureM token: {e}")
            diagnostics["error"] = "request_exception"
            diagnostics["exception"] = str(e)
            return None, None, diagnostics

    @staticmethod
    def get_access_token(db: Session) -> Optional[str]:
        env_access_token = os.getenv("SUREM_ACCESS_TOKEN")
        env_expires_at = os.getenv("SUREM_TOKEN_EXPIRES_AT")

        try:
            SureMService._acquire_lock(db)

            token_row = db.query(ServiceToken).filter(ServiceToken.service_name == SureMService.TOKEN_SERVICE_NAME).first()
            if token_row and SureMService._token_is_valid(token_row.access_token, token_row.expires_at, SureMService.TOKEN_REFRESH_MARGIN):
                logger.debug("Using cached SureM access token from database.")
                return token_row.access_token

            if env_access_token:
                try:
                    parsed_env_expiry = SureMService._parse_timestamp(env_expires_at)
                    if SureMService._token_is_valid(env_access_token, parsed_env_expiry, SureMService.TOKEN_REFRESH_MARGIN):
                        SureMService._upsert_secret(db, SureMService.TOKEN_SERVICE_NAME, env_access_token, parsed_env_expiry)
                        db.commit()
                        logger.info("Seeded SureM access token cache from environment.")
                        return env_access_token
                except ValueError:
                    logger.warning(f"Invalid SUREM_TOKEN_EXPIRES_AT format: {env_expires_at}")

            new_token, new_expires_at, _ = SureMService._request_new_access_token()
            if not new_token:
                return None

            SureMService._upsert_secret(db, SureMService.TOKEN_SERVICE_NAME, new_token, new_expires_at)
            db.commit()
            return new_token
        except Exception as e:
            db.rollback()
            logger.error(f"Error caching SureM access token: {e}")
            return None
        finally:
            try:
                SureMService._release_lock(db)
            except Exception as unlock_error:
                logger.warning(f"Failed to release SureM advisory lock: {unlock_error}")

    @staticmethod
    def _get_persisted_image_key(db: Session, filename: str) -> Optional[Dict[str, str]]:
        row = db.query(ServiceToken).filter(ServiceToken.service_name == f"{SureMService.IMAGE_CACHE_PREFIX}{filename}").first()
        if row and SureMService._token_is_valid(row.access_token, row.expires_at, SureMService.IMAGE_REFRESH_MARGIN):
            normalized_expires_at = SureMService._normalize_expires_at(row.expires_at)
            return {
                "imageKey": row.access_token,
                "expiryDate": normalized_expires_at.isoformat() if normalized_expires_at else "",
            }
        return None

    @staticmethod
    def _persist_image_key(db: Session, filename: str, image_key: str, expiry_date: Optional[str]) -> None:
        parsed_expiry = SureMService._parse_timestamp(expiry_date)
        SureMService._upsert_secret(db, f"{SureMService.IMAGE_CACHE_PREFIX}{filename}", image_key, parsed_expiry)
        db.commit()

    @staticmethod
    def debug_auth_status_direct(db: Session) -> Dict[str, Any]:
        token_row = db.query(ServiceToken).filter(ServiceToken.service_name == SureMService.TOKEN_SERVICE_NAME).first()
        env_access_token = os.getenv("SUREM_ACCESS_TOKEN")
        env_expires_at = os.getenv("SUREM_TOKEN_EXPIRES_AT")

        result: Dict[str, Any] = {
            "status": "error",
            "auth_url_present": bool(os.getenv("SUREM_AUTH_URL")),
            "user_code_present": bool(os.getenv("SUREM_USER_CODE")),
            "secret_key_present": bool(os.getenv("SUREM_SECRET_KEY")),
            "env_token_present": bool(env_access_token),
            "env_token_expires_at_present": bool(env_expires_at),
            "db_token_present": bool(token_row and token_row.access_token),
            "db_token_expires_at": token_row.expires_at.isoformat() if token_row and token_row.expires_at else None,
        }

        if token_row and SureMService._token_is_valid(token_row.access_token, token_row.expires_at, SureMService.TOKEN_REFRESH_MARGIN):
            result.update({
                "status": "success",
                "message": "Authentication successful using cached database token.",
                "source": "database",
            })
            return result

        if env_access_token:
            try:
                parsed_env_expiry = SureMService._parse_timestamp(env_expires_at)
                if SureMService._token_is_valid(env_access_token, parsed_env_expiry, SureMService.TOKEN_REFRESH_MARGIN):
                    result.update({
                        "status": "success",
                        "message": "Authentication successful using environment token.",
                        "source": "environment",
                        "env_token_expires_at": parsed_env_expiry.isoformat() if parsed_env_expiry else None,
                    })
                    return result
            except ValueError:
                result["env_token_error"] = "invalid_timestamp"

        _, _, diagnostics = SureMService._request_new_access_token()
        result.update(diagnostics)
        if diagnostics.get("source") == "fresh_auth":
            result.update({
                "status": "success",
                "message": "Authentication successful using a freshly issued token.",
                "source": "fresh_auth",
            })
        else:
            result.setdefault("message", "Failed to retrieve access token.")
        return result

    @staticmethod
    def debug_auth_status(db: Session) -> Dict[str, Any]:
        if SureMService._broker_enabled():
            result = SureMService._broker_request("GET", "/api/test/broker/test-auth")
            result.setdefault("broker_enabled", True)
            result.setdefault("broker_url", SureMService._broker_base_url())
            return result
        result = SureMService.debug_auth_status_direct(db)
        result.setdefault("broker_enabled", False)
        return result

    @staticmethod
    def send_sms_direct(db: Session, text: str) -> Dict[str, Any]:
        token = SureMService.get_access_token(db)
        if not token:
            return {"status": "error", "message": "Failed to get SUREM_ACCESS_TOKEN."}

        payload = {"to": "01033903190", "text": text, "reqPhone": "025761112"}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        try:
            response = requests.post("https://rest.surem.com/api/v1/send/sms", headers=headers, json=payload, timeout=10)
            data = response.json()
            if response.status_code == 200 and data.get("code") == "A0000":
                return {"status": "success", "code": data.get("code"), "data": data}
            logger.error(f"SureM send_sms Error: {data}")
            return {"status": "error", "code": data.get("code"), "message": data.get("message", "Unknown error")}
        except Exception as e:
            logger.error(f"SureM send_sms Exception: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_sms(db: Session, text: str) -> Dict[str, Any]:
        if SureMService._broker_enabled():
            return SureMService._broker_request("POST", "/api/test/broker/send-sms", json_body={"text": text})
        return SureMService.send_sms_direct(db, text)

    @staticmethod
    def upload_image_direct(db: Session, file_content: bytes, filename: str) -> Dict[str, Any]:
        cached = SureMService._get_persisted_image_key(db, filename)
        if cached:
            logger.info(f"Using cached SureM imageKey for {filename}")
            return {"status": "success", "data": cached, "cached": True}

        token = SureMService.get_access_token(db)
        if not token:
            return {"status": "error", "message": "Failed to get SUREM_ACCESS_TOKEN."}

        try:
            logger.info(f"Uploading new image to SureM: {filename}")
            response = requests.post(
                "https://rest.surem.com/api/v1/image",
                headers={"Authorization": f"Bearer {token}"},
                files={"image1": (filename, file_content, "image/jpeg")},
                timeout=15,
            )
            data = response.json()
            if response.status_code == 200 and data.get("code") == "A0000":
                result_data = data.get("data", {})
                image_key = result_data.get("imageKey")
                expiry = result_data.get("expiryDate")
                if image_key:
                    SureMService._persist_image_key(db, filename, image_key, expiry)
                return {"status": "success", "code": data.get("code"), "data": result_data, "cached": False}
            logger.error(f"SureM upload_image Error: {data}")
            return {"status": "error", "code": data.get("code"), "message": data.get("message", "Unknown error for image upload")}
        except Exception as e:
            logger.error(f"SureM upload_image Exception: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def upload_image(db: Session, file_content: bytes, filename: str) -> Dict[str, Any]:
        if SureMService._broker_enabled():
            return SureMService._broker_request(
                "POST",
                "/api/test/broker/upload-image",
                files={"file": (filename, file_content, "image/jpeg")},
            )
        return SureMService.upload_image_direct(db, file_content, filename)

    @staticmethod
    def send_mms_direct(db: Session, subject: str, text: str, image_key: Optional[str] = None) -> Dict[str, Any]:
        token = SureMService.get_access_token(db)
        if not token:
            return {"status": "error", "message": "Failed to get SUREM_ACCESS_TOKEN."}

        payload: Dict[str, Any] = {
            "to": "01097343368",
            "subject": subject,
            "text": text,
            "reqPhone": "025761112",
        }
        if image_key:
            payload["imageKey"] = image_key

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        try:
            response = requests.post("https://rest.surem.com/api/v1/send/mms", headers=headers, json=payload, timeout=10)
            data = response.json()
            if response.status_code == 200 and data.get("code") == "A0000":
                return {"status": "success", "code": data.get("code"), "data": data}
            logger.error(f"SureM send_mms Error: {data}")
            return {"status": "error", "code": data.get("code"), "message": data.get("message", "Unknown error")}
        except Exception as e:
            logger.error(f"SureM send_mms Exception: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_mms(db: Session, subject: str, text: str, image_key: Optional[str] = None) -> Dict[str, Any]:
        if SureMService._broker_enabled():
            return SureMService._broker_request(
                "POST",
                "/api/test/broker/send-mms",
                json_body={"subject": subject, "text": text, "image_key": image_key},
            )
        return SureMService.send_mms_direct(db, subject, text, image_key)
