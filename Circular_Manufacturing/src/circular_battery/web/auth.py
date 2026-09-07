"""Deployment-boundary authentication and role authorization.

The local Studio remains loopback-only and may run without authentication. Any
non-loopback or production deployment must explicitly configure the bearer
bootstrap contract below. This is a fail-closed bridge for a restricted pilot;
enterprise OIDC/SAML and centralized RBAC should normally be enforced at the
approved identity-aware ingress.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
import os
import re
from typing import Mapping


ROLE_RANK = {"viewer": 10, "operator": 20, "admin": 30}
TOKEN_DIGEST_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
VALID_DEPLOYMENT_MODES = {"local", "staging", "production"}
VALID_AUTH_MODES = {"disabled", "bearer"}
PUBLIC_ROUTES = {"/api/v1/health", "/api/health", "/health"}


class DeploymentConfigurationError(RuntimeError):
    """The process is not safely configured for its requested bind."""


class AuthenticationError(Exception):
    def __init__(self, code: str, message: str, status: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class AuthConfig:
    deployment_mode: str
    auth_mode: str
    token_digest: str | None
    role: str

    def authorize(self, headers: Mapping[str, str], required_role: str | None) -> None:
        if required_role is None or self.auth_mode == "disabled":
            return
        if required_role not in ROLE_RANK:
            raise DeploymentConfigurationError(f"Unknown required role: {required_role}")

        authorization = headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token or len(token) > 4096:
            raise AuthenticationError("AUTHENTICATION_REQUIRED", "A bearer credential is required for this endpoint.", 401)

        candidate_digest = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
        if not self.token_digest or not hmac.compare_digest(candidate_digest, self.token_digest):
            raise AuthenticationError("AUTHENTICATION_FAILED", "Bearer credential was rejected.", 401)
        if ROLE_RANK[self.role] < ROLE_RANK[required_role]:
            raise AuthenticationError("FORBIDDEN", "The credential is not authorized for this endpoint.", 403)


def is_loopback_host(host: str) -> bool:
    normalized = (host or "").strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def load_auth_config(env: Mapping[str, str] | None = None, *, bind_host: str | None = None) -> AuthConfig:
    values = os.environ if env is None else env
    deployment_mode = values.get("CIRCULAR_DEPLOYMENT_MODE", "local").strip().lower()
    auth_mode = values.get("CIRCULAR_AUTH_MODE", "disabled").strip().lower()
    if deployment_mode not in VALID_DEPLOYMENT_MODES:
        raise DeploymentConfigurationError("CIRCULAR_DEPLOYMENT_MODE must be local, staging, or production.")
    if auth_mode not in VALID_AUTH_MODES:
        raise DeploymentConfigurationError("CIRCULAR_AUTH_MODE must be disabled or bearer.")
    if bind_host and not is_loopback_host(bind_host) and auth_mode == "disabled":
        raise DeploymentConfigurationError("Non-loopback binds require explicit bearer authentication.")
    if deployment_mode == "production" and auth_mode != "bearer":
        raise DeploymentConfigurationError("Production mode requires explicit bearer authentication.")

    role = values.get("CIRCULAR_API_ROLE", "operator").strip().lower()
    if role not in ROLE_RANK:
        raise DeploymentConfigurationError("CIRCULAR_API_ROLE must be viewer, operator, or admin.")

    token_digest = values.get("CIRCULAR_API_TOKEN_SHA256", "").strip().lower()
    if auth_mode == "bearer" and not TOKEN_DIGEST_PATTERN.fullmatch(token_digest):
        raise DeploymentConfigurationError("Bearer mode requires a 64-character CIRCULAR_API_TOKEN_SHA256.")
    return AuthConfig(deployment_mode, auth_mode, token_digest or None, role)


def required_role(path: str, method: str) -> str | None:
    """Return the minimum role for an API route; static assets stay public."""
    if path in PUBLIC_ROUTES or not path.startswith("/api"):
        return None
    if method == "GET":
        return "admin" if path == "/api/v1/audit" else "viewer"
    if method == "POST":
        return "operator"
    if method == "DELETE":
        return "admin"
    return "viewer"


def authorize_request(headers: Mapping[str, str], path: str, method: str, *, bind_host: str | None = None, env: Mapping[str, str] | None = None) -> None:
    config = load_auth_config(env, bind_host=bind_host)
    config.authorize(headers, required_role(path, method))


def validate_server_configuration(host: str, env: Mapping[str, str] | None = None) -> AuthConfig:
    return load_auth_config(env, bind_host=host)
