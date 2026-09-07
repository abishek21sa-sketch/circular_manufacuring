from __future__ import annotations

import hashlib

import pytest

from circular_battery.web.auth import DeploymentConfigurationError, load_auth_config
from scripts.production_preflight import build_preflight


def test_disabled_auth_is_loopback_only():
    env={"CIRCULAR_DEPLOYMENT_MODE":"local","CIRCULAR_AUTH_MODE":"disabled"}
    assert load_auth_config(env,bind_host="127.0.0.1").auth_mode=="disabled"
    with pytest.raises(DeploymentConfigurationError):
        load_auth_config(env,bind_host="0.0.0.0")


def test_bearer_config_accepts_digest_without_storing_raw_token():
    token="T"*48
    digest=hashlib.sha256(token.encode()).hexdigest()
    config=load_auth_config({"CIRCULAR_AUTH_MODE":"bearer","CIRCULAR_API_TOKEN_SHA256":digest},bind_host="0.0.0.0")
    assert config.token_digest==digest
    assert token not in repr(config)


def test_preflight_passes_local_and_blocks_unready_production():
    local=build_preflight({"CIRCULAR_DEPLOYMENT_MODE":"local","CIRCULAR_AUTH_MODE":"disabled"},host="127.0.0.1")
    assert local["passed"] is True

    token="T"*48
    production=build_preflight({
        "CIRCULAR_DEPLOYMENT_MODE":"production",
        "CIRCULAR_AUTH_MODE":"bearer",
        "CIRCULAR_API_TOKEN_SHA256":hashlib.sha256(token.encode()).hexdigest(),
        "CIRCULAR_API_ROLE":"operator",
    },host="0.0.0.0")
    assert production["passed"] is False
    assert production["checks"]["bind_and_authentication"]["status"]=="PASS"
    assert production["checks"]["production_database"]["status"]=="PENDING"
    assert production["checks"]["external_production_attestations"]["status"]=="PENDING"


def test_production_database_requires_operational_evidence():
    env={
        "CIRCULAR_DEPLOYMENT_MODE":"production",
        "CIRCULAR_AUTH_MODE":"bearer",
        "CIRCULAR_API_TOKEN_SHA256":"a"*64,
        "CIRCULAR_API_ROLE":"operator",
        "CIRCULAR_PLATFORM_DB_BACKEND":"postgres",
        "CIRCULAR_DATABASE_URL":"postgresql://redacted",
    }
    report=build_preflight(env,host="0.0.0.0")
    assert report["checks"]["bind_and_authentication"]["status"]=="PASS"
    assert report["checks"]["production_database"]["status"]=="PENDING"
    env.update({
        "CIRCULAR_DATABASE_MIGRATION_STATUS":"approved",
        "CIRCULAR_DATABASE_BACKUP_STATUS":"approved",
        "CIRCULAR_DATABASE_CONCURRENCY_STATUS":"approved",
    })
    report=build_preflight(env,host="0.0.0.0")
    assert report["checks"]["production_database"]["status"]=="PASS"
