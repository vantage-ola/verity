from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class Feature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    status: Literal["active", "deprecated", "retired"] = "active"

    @field_validator("id")
    @classmethod
    def _id_prefix(cls, v: str) -> str:
        if not v.startswith("feat:"):
            raise ValueError(f"Feature id must start with 'feat:', got '{v}'")
        return v


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    feature_id: str
    title: str
    tier: Literal["T1", "T2", "T3"] = "T1"
    status: Literal["open", "verified", "rejected"] = "open"

    @field_validator("id")
    @classmethod
    def _id_prefix(cls, v: str) -> str:
        if not v.startswith("clm:"):
            raise ValueError(f"Claim id must start with 'clm:', got '{v}'")
        return v


class Test(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    claim_id: str
    kind: Literal["unit", "integration"]
    path: str
    status: Literal["pending", "passing", "failing"] = "pending"

    @field_validator("id")
    @classmethod
    def _id_prefix(cls, v: str) -> str:
        if not v.startswith("tst:"):
            raise ValueError(f"Test id must start with 'tst:', got '{v}'")
        return v


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    test_id: str
    kind: Literal["test_run"] = "test_run"
    artifact_path: str
    status: Literal["passed", "failed", "collected"] = "collected"

    @field_validator("id")
    @classmethod
    def _id_prefix(cls, v: str) -> str:
        if not v.startswith("evd:"):
            raise ValueError(f"Evidence id must start with 'evd:', got '{v}'")
        return v


class Release(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    timestamp: str
    walrus_blob_id: str | None = None
    claim_ids: list[str] = []

    @field_validator("id")
    @classmethod
    def _id_prefix(cls, v: str) -> str:
        if not v.startswith("rel:"):
            raise ValueError(f"Release id must start with 'rel:', got '{v}'")
        return v


class PushRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blob_id: str
    timestamp: str
    backend: Literal["walrus", "memwal"] = "walrus"
    signature: str | None = None      # base64 Ed25519 sig over blob_id bytes
    signer_pubkey: str | None = None  # base64 raw Ed25519 public key (32 bytes)


class ContextEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    value: str


class Registry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1.0"
    repo_id: str
    context: list[ContextEntry] = []
    features: list[Feature] = []
    claims: list[Claim] = []
    tests: list[Test] = []
    evidence: list[Evidence] = []
    releases: list[Release] = []
    pushes: list[PushRecord] = []
