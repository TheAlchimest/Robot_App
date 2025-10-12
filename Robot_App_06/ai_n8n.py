# ai_n8n.py
# -------------------------------------------------------------------
# Robust n8n chat client with timeout, retries, and strict JSON parsing.
# -------------------------------------------------------------------
import time
import requests
from Config import Config

class N8nClient:
    def __init__(self, config: Config | None = None):
        self.cfg = config or Config()
        self.url = self.cfg.N8N_URL
        self.timeout = self.cfg.HTTP_TIMEOUT
        self.retries = self.cfg.RETRIES

    def chat(self, session_id: str, message: str) -> str:
        if not message:
            return ""
        headers = {"Content-Type": "application/json"}
        payload = {"sessionId": session_id, "message": message}

        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.post(self.url, headers=headers, json=payload,
                                     timeout=self.timeout, verify=True)
                resp.raise_for_status()
                try:
                    js = resp.json()
                except ValueError:
                    return resp.text.strip()

                if isinstance(js, dict):
                    out = js.get("output", "") or js.get("message", "")
                    return (out or "").strip()

                # Unexpected shape → stringify
                return str(js).strip()

            except requests.RequestException as e:
                if attempt == self.retries:
                    print(f"[n8n] error(final): {e}")
                    return ""
                time.sleep(0.5 * attempt)

        return ""
