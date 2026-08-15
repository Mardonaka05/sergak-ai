"""One-time password generation and verification (in-memory store)"""
import random
import time
from typing import Optional, Dict


class OTPStore:
    """Simple in-memory OTP store with TTL"""
    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self._store: Dict[str, dict] = {}

    def generate(self, key: str) -> str:
        """Generate a 6-digit code and store it"""
        code = f"{random.randint(0, 999999):06d}"
        self._store[key.lower()] = {
            "code": code,
            "expires_at": time.time() + self.ttl,
            "attempts": 0,
        }
        return code

    def verify(self, key: str, code: str) -> bool:
        """Verify code, return True/False. Single-use — consumes on success."""
        entry = self._store.get(key.lower())
        if not entry:
            return False
        if time.time() > entry["expires_at"]:
            self._store.pop(key.lower(), None)
            return False
        entry["attempts"] += 1
        if entry["attempts"] > 5:
            self._store.pop(key.lower(), None)
            return False
        if entry["code"] == str(code).strip():
            self._store.pop(key.lower(), None)
            return True
        return False

    def get_remaining_seconds(self, key: str) -> int:
        entry = self._store.get(key.lower())
        if not entry:
            return 0
        return max(0, int(entry["expires_at"] - time.time()))


otp_store = OTPStore(ttl_seconds=600)  # 10 minute TTL
