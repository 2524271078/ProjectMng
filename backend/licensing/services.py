import base64
import hashlib
import json
import os
import platform
from datetime import date, timedelta
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

from licensing.models import LicenseState


REQUIRED_FIELDS = {"version", "license_id", "customer", "issued_at", "expires_at", "machine_fingerprint"}


def canonical_payload(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def get_machine_fingerprint():
    machine_id = ""
    for candidate in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            machine_id = Path(candidate).read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if machine_id:
            break
    if not machine_id:
        machine_id = f"{platform.node()}:{os.getpid()}"
    return hashlib.sha256(f"ProjectMng-License-v1:{machine_id}".encode("utf-8")).hexdigest()


def _load_public_key():
    key_path = Path(settings.LICENSE_PUBLIC_KEY_PATH)
    if not key_path.exists():
        raise ValueError("public_key_missing")
    return serialization.load_pem_public_key(key_path.read_bytes())


def verify_envelope(envelope):
    if not isinstance(envelope, dict):
        raise ValueError("license_format_invalid")
    payload = envelope.get("payload")
    signature = envelope.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        raise ValueError("license_format_invalid")
    if not REQUIRED_FIELDS.issubset(payload):
        raise ValueError("license_payload_incomplete")
    if payload.get("version") != 1:
        raise ValueError("license_version_unsupported")
    try:
        raw_signature = base64.b64decode(signature.encode("ascii"), validate=True)
        _load_public_key().verify(raw_signature, canonical_payload(payload))
    except (ValueError, TypeError, InvalidSignature):
        raise ValueError("license_signature_invalid")
    if payload.get("machine_fingerprint") != get_machine_fingerprint():
        raise ValueError("license_machine_mismatch")
    try:
        expires_at = date.fromisoformat(payload["expires_at"])
        date.fromisoformat(payload["issued_at"])
    except (TypeError, ValueError):
        raise ValueError("license_date_invalid")
    if expires_at < date.today():
        raise ValueError("license_expired")
    return payload


def _inactive(reason, **extra):
    return {"active": False, "reason": reason, "machine_fingerprint": get_machine_fingerprint(), **extra}


def get_license_status(record_activity=True):
    if not settings.LICENSE_ENFORCEMENT_ENABLED:
        return {
            "active": True,
            "reason": "development_mode",
            "machine_fingerprint": get_machine_fingerprint(),
            "enforcement_enabled": False,
        }
    try:
        state = LicenseState.get_solo()
    except (OperationalError, ProgrammingError):
        return _inactive("license_not_initialized", enforcement_enabled=True)
    if not state.license_payload or not state.signature:
        return _inactive("license_missing", enforcement_enabled=True)
    try:
        payload = verify_envelope({"payload": state.license_payload, "signature": state.signature})
    except ValueError as error:
        state.last_validation_error = str(error)
        state.save(update_fields=["last_validation_error", "updated_at"])
        return _inactive(str(error), enforcement_enabled=True, payload=state.license_payload)

    now = timezone.now()
    if state.last_seen_at and now + timedelta(minutes=5) < state.last_seen_at:
        state.last_validation_error = "system_time_rollback"
        state.save(update_fields=["last_validation_error", "updated_at"])
        return _inactive("system_time_rollback", enforcement_enabled=True, payload=payload)
    if record_activity and (not state.last_seen_at or now - state.last_seen_at >= timedelta(minutes=5)):
        state.last_seen_at = now
        state.last_validation_error = ""
        state.save(update_fields=["last_seen_at", "last_validation_error", "updated_at"])
    return {
        "active": True,
        "reason": "active",
        "machine_fingerprint": get_machine_fingerprint(),
        "enforcement_enabled": True,
        "payload": payload,
    }


def activate_license(envelope):
    payload = verify_envelope(envelope)
    state = LicenseState.get_solo()
    state.license_payload = payload
    state.signature = envelope["signature"]
    state.activated_at = timezone.now()
    state.last_seen_at = timezone.now()
    state.last_validation_error = ""
    state.save()
    return get_license_status(record_activity=False)
