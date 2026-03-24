import os
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SureMService:
    @staticmethod
    def get_access_token() -> str:
        """
        Retrieves the access token from environment variables or fetches a new one if expired.
        Updates the .env file with the new token and expiration time.
        """
        user_code = os.getenv("SUREM_USER_CODE")
        secret_key = os.getenv("SUREM_SECRET_KEY")
        auth_url = os.getenv("SUREM_AUTH_URL")
        
        if not all([user_code, secret_key, auth_url]):
            logger.error("SureM credentials missing in environment variables.")
            return None

        access_token = os.getenv("SUREM_ACCESS_TOKEN")
        expires_at_str = os.getenv("SUREM_TOKEN_EXPIRES_AT")

        # Check if token exists and is still valid
        if access_token and expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                # Refresh 5 minutes before actual expiration for safety
                if datetime.now() < expires_at - timedelta(minutes=5):
                    logger.debug("Using cached SureM access token.")
                    return access_token
            except ValueError:
                logger.warning(f"Invalid expiration date format in .env: {expires_at_str}")

        # Token is missing or expired, fetch a new one
        logger.info("Fetching new SureM access token.")
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "userCode": user_code,
                "secretKey": secret_key
            }
            response = requests.post(auth_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "A0000":
                    new_token = data.get("data", {}).get("accessToken")
                    expires_in_seconds = data.get("data", {}).get("expiresIn", 3600)
                    
                    if new_token:
                        # Calculate expiration time
                        new_expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
                        new_expires_at_str = new_expires_at.isoformat()
                        
                        # Update environment variables for the current process
                        os.environ["SUREM_ACCESS_TOKEN"] = new_token
                        os.environ["SUREM_TOKEN_EXPIRES_AT"] = new_expires_at_str
                        
                        # Update the .env file
                        SureMService._update_env_file("SUREM_ACCESS_TOKEN", new_token)
                        SureMService._update_env_file("SUREM_TOKEN_EXPIRES_AT", new_expires_at_str)
                        
                        logger.info(f"Successfully refreshed SureM token. Expires at: {new_expires_at_str}")
                        return new_token
                else:
                    logger.error(f"SureM Auth Error: Code {data.get('code')}, {data}")
            else:
                logger.error(f"SureM Auth HTTP Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to fetch SureM token: {e}")
        
        return None

    @staticmethod
    def _update_env_file(key: str, value: str):
        """Helper to update keys in the .env file."""
        env_path = "/Users/sangyeol.park@gruve.ai/Documents/D4/.env"
        if not os.path.exists(env_path):
            return

        with open(env_path, 'r') as file:
            lines = file.readlines()

        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        if not key_found:
            lines.append(f"{key}={value}\n")

        with open(env_path, 'w') as file:
            file.writelines(lines)

    @staticmethod
    def send_sms(text: str) -> dict:
        url = "https://rest.surem.com/api/v1/send/sms"
        token = SureMService.get_access_token()
        
        if not token:
            return {"status": "error", "message": "Failed to get SUREM_ACCESS_TOKEN."}
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "to": "01033903190",
            "text": text,
            "reqPhone": "025761112"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()
            # If "code": "A0000", it means the message was sent successfully.
            if response.status_code == 200 and data.get("code") == "A0000":
                return {"status": "success", "code": data.get("code"), "data": data}
            else:
                logger.error(f"SureM send_sms Error: {data}")
                return {"status": "error", "code": data.get("code"), "message": data.get("message", "Unknown error")}
        except Exception as e:
            logger.error(f"SureM send_sms Exception: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_storage_path() -> str:
        path = "/Users/sangyeol.park@gruve.ai/Documents/D4/app/storage"
        os.makedirs(path, exist_ok=True)
        return os.path.join(path, "surem_images.json")

    @staticmethod
    def _get_persisted_image_key(filename: str) -> dict:
        """Returns the {imageKey, expiryDate} or None if expired/not-found"""
        import json
        storage_file = SureMService.get_storage_path()
        if not os.path.exists(storage_file):
            return None
            
        try:
            with open(storage_file, 'r') as f:
                data = json.load(f)
                
            if filename in data:
                entry = data[filename]
                expiry_str = entry.get("expiryDate")
                if expiry_str:
                    from datetime import datetime
                    # Parse assuming ISO 8601 formatting
                    # using fromisoformat (handles standard format well, but offset might differ, let's just do a basic check)
                    try:
                        expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                        # Just a basic safety margin, require at least 1 hour of validity
                        if datetime.now().astimezone() < expiry - timedelta(hours=1):
                            return entry
                    except ValueError:
                        pass # proceed to re-upload on parsing error
        except Exception as e:
            logger.error(f"Error reading SUREM image keys: {e}")
        return None

    @staticmethod
    def _persist_image_key(filename: str, image_key: str, expiry_date: str):
        import json
        storage_file = SureMService.get_storage_path()
        data = {}
        if os.path.exists(storage_file):
            try:
                with open(storage_file, 'r') as f:
                    data = json.load(f)
            except Exception:
                pass
                
        data[filename] = {
            "imageKey": image_key,
            "expiryDate": expiry_date,
            "uploadedAt": datetime.now().isoformat()
        }
        
        try:
            with open(storage_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving SUREM image keys: {e}")

    @staticmethod
    def upload_image(file_content: bytes, filename: str) -> dict:
        """Uploads an image to SureM and returns the imageKey. Reuses keys if valid."""
        
        # Check cache first
        cached = SureMService._get_persisted_image_key(filename)
        if cached:
            logger.info(f"Using cached SureM imageKey for {filename}")
            return {"status": "success", "data": cached, "cached": True}
            
        url = "https://rest.surem.com/api/v1/image"
        token = SureMService.get_access_token()
        
        if not token:
            return {"status": "error", "message": "Failed to get SUREM_ACCESS_TOKEN."}
            
        headers = {
            "Authorization": f"Bearer {token}"
            # Content-Type is set automatically by requests for multipart/form-data
        }
        
        files = {
            "image1": (filename, file_content, "image/jpeg")
        }
        
        try:
            logger.info(f"Uploading new image to SureM: {filename}")
            response = requests.post(url, headers=headers, files=files, timeout=15)
            data = response.json()
            
            if response.status_code == 200 and data.get("code") == "A0000":
                result_data = data.get("data", {})
                image_key = result_data.get("imageKey")
                expiry = result_data.get("expiryDate")
                
                if image_key and expiry:
                    SureMService._persist_image_key(filename, image_key, expiry)
                
                return {"status": "success", "code": data.get("code"), "data": result_data, "cached": False}
            else:
                logger.error(f"SureM upload_image Error: {data}")
                return {"status": "error", "code": data.get("code"), "message": data.get("message", "Unknown error for image upload")}
        except Exception as e:
            logger.error(f"SureM upload_image Exception: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_mms(subject: str, text: str, image_key: str = None) -> dict:
        url = "https://rest.surem.com/api/v1/send/mms"
        token = SureMService.get_access_token()
        
        if not token:
            return {"status": "error", "message": "Failed to get SUREM_ACCESS_TOKEN."}
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "to": "01097343368",
            "subject": subject,
            "text": text,
            "reqPhone": "025761112"
        }
        
        if image_key:
            payload["imageKey"] = image_key
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()
            # If "code": "A0000", it means the message was sent successfully.
            if response.status_code == 200 and data.get("code") == "A0000":
                return {"status": "success", "code": data.get("code"), "data": data}
            else:
                logger.error(f"SureM send_mms Error: {data}")
                return {"status": "error", "code": data.get("code"), "message": data.get("message", "Unknown error")}
        except Exception as e:
            logger.error(f"SureM send_mms Exception: {e}")
            return {"status": "error", "message": str(e)}

