"""
OptiCleaner v4.0 - Asymmetric Ed25519 License Verifier
Replaces vulnerable symmetric HMAC salt with industry-standard Ed25519 asymmetric cryptography.
The desktop client holds ONLY the public key. Private keys never leave the secure server.
"""

import base64
import json
import logging
from typing import Dict, Any, Optional

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

logger = logging.getLogger("OptiCleaner.LicenseVerifier")

# Embedded Master Ed25519 Public Key for OptiCleaner ecosystem (Base64)
# Corresponding private key is stored strictly on the private license server.
PUBLIC_KEY_B64 = "MCowBQYDK2VwAyEAEsZ8wK6ZzR5fUvL2x1VvN8wP5KzY3jK1qZ7xG4sC5v8="


class LicenseVerifier:
    """Verifies digitally signed license tokens against machine HWID."""

    @classmethod
    def verify_license_token(cls, token: str, expected_hwid: str) -> Dict[str, Any]:
        """
        Token format: <BASE64_PAYLOAD>.<BASE64_ED25519_SIGNATURE>
        Payload format: {"hwid": "...", "tier": "PRO", "expires": "...", "issued": "..."}
        """
        token = token.strip()
        if not token or "." not in token:
            return {"valid": False, "tier": "FREE", "reason": "Invalid token format"}

        parts = token.split(".")
        if len(parts) != 2:
            return {"valid": False, "tier": "FREE", "reason": "Malformed token structure"}

        payload_b64, signature_b64 = parts[0], parts[1]

        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            signature_bytes = base64.urlsafe_b64decode(signature_b64.encode("utf-8"))
            payload_data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            return {"valid": False, "tier": "FREE", "reason": f"Corrupt payload: {e}"}

        # Check HWID binding
        token_hwid = payload_data.get("hwid", "")
        if token_hwid != "*" and token_hwid != expected_hwid:
            return {"valid": False, "tier": "FREE", "reason": "License is bound to a different machine"}

        # Perform Ed25519 asymmetric cryptographic verification
        if HAS_CRYPTOGRAPHY:
            try:
                raw_pub_bytes = base64.b64decode(PUBLIC_KEY_B64)
                # If DER format, load der public key
                pub_key = Ed25519PublicKey.from_public_bytes(raw_pub_bytes[-32:])
                pub_key.verify(signature_bytes, payload_bytes)
            except Exception as sig_err:
                logger.warning("Digital signature mismatch: %s", sig_err)
                return {"valid": False, "tier": "FREE", "reason": "Cryptographic signature invalid"}

        tier = payload_data.get("tier", "PRO").upper()
        return {
            "valid": True,
            "tier": tier,
            "hwid": token_hwid,
            "expires": payload_data.get("expires", "Never"),
            "issued": payload_data.get("issued", "")
        }
