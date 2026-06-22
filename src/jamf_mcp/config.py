import os
from dataclasses import dataclass


@dataclass
class JamfProConfig:
    url: str
    client_id: str
    client_secret: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> "JamfProConfig":
        return cls(
            url=os.environ.get("JAMF_PRO_URL", "").rstrip("/"),
            client_id=os.environ.get("JAMF_CLIENT_ID", ""),
            client_secret=os.environ.get("JAMF_CLIENT_SECRET", ""),
            username=os.environ.get("JAMF_USERNAME", ""),
            password=os.environ.get("JAMF_PASSWORD", ""),
        )

    @property
    def configured(self) -> bool:
        return bool(self.url) and (
            (bool(self.client_id) and bool(self.client_secret))
            or (bool(self.username) and bool(self.password))
        )

    @property
    def uses_oauth(self) -> bool:
        return bool(self.client_id) and bool(self.client_secret)

    def missing_vars(self) -> list[str]:
        missing = []
        if not self.url:
            missing.append("JAMF_PRO_URL")
        if not self.uses_oauth and not (self.username and self.password):
            missing += ["JAMF_CLIENT_ID + JAMF_CLIENT_SECRET", "(or JAMF_USERNAME + JAMF_PASSWORD)"]
        return missing


@dataclass
class JamfProtectConfig:
    url: str
    client_id: str
    password: str

    @classmethod
    def from_env(cls) -> "JamfProtectConfig":
        return cls(
            url=os.environ.get("JAMF_PROTECT_URL", "").rstrip("/"),
            client_id=os.environ.get("JAMF_PROTECT_CLIENT_ID", ""),
            password=os.environ.get("JAMF_PROTECT_PASSWORD", ""),
        )

    @property
    def configured(self) -> bool:
        return bool(self.url) and bool(self.client_id) and bool(self.password)

    def missing_vars(self) -> list[str]:
        missing = []
        if not self.url:
            missing.append("JAMF_PROTECT_URL")
        if not self.client_id:
            missing.append("JAMF_PROTECT_CLIENT_ID")
        if not self.password:
            missing.append("JAMF_PROTECT_PASSWORD")
        return missing


@dataclass
class JamfSecurityConfig:
    client_id: str
    client_secret: str
    region: str

    @classmethod
    def from_env(cls) -> "JamfSecurityConfig":
        return cls(
            client_id=os.environ.get("JAMF_SECURITY_CLIENT_ID", ""),
            client_secret=os.environ.get("JAMF_SECURITY_CLIENT_SECRET", ""),
            region=os.environ.get("JAMF_SECURITY_REGION", "us").lower(),
        )

    @property
    def configured(self) -> bool:
        return bool(self.client_id) and bool(self.client_secret)

    @property
    def api_base(self) -> str:
        if self.region == "eu":
            return "https://api.eu.wandera.com"
        return "https://api.wandera.com"

    @property
    def auth_base(self) -> str:
        if self.region == "eu":
            return "https://auth.eu.wandera.com"
        return "https://auth.wandera.com"

    def missing_vars(self) -> list[str]:
        missing = []
        if not self.client_id:
            missing.append("JAMF_SECURITY_CLIENT_ID")
        if not self.client_secret:
            missing.append("JAMF_SECURITY_CLIENT_SECRET")
        return missing
