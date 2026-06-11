from enum import Enum


class InstallStatus(str, Enum):
    SUCCESS     = "success"
    FAILED      = "failed"
    INCOMPATIBLE = "incompatible"
    ALREADY_INSTALLED = "already_installed"


class RemoveStatus(str, Enum):
    SUCCESS = "success"
    FAILED  = "failed"
    NOT_FOUND = "not_found"


class UpdateStatus(str, Enum):
    SUCCESS     = "success"
    FAILED      = "failed"
    INCOMPATIBLE = "incompatible"
    UP_TO_DATE   = "up_to_date"
    NOT_FOUND    = "not_found"


class TrustLevel(str, Enum):
    """
    Trust level for a package source.
    Phase 5 will populate this based on cryptographic signature verification.
    """
    VERIFIED   = "verified"    # signed by a trusted publisher
    COMMUNITY  = "community"   # signed but publisher not in trust list
    UNSIGNED   = "unsigned"    # no signature present (Phase 3 default)
    UNTRUSTED  = "untrusted"   # signature verification failed


class CompatibilityLevel(str, Enum):
    COMPATIBLE   = "compatible"
    WARNING      = "warning"     # within range but close to boundary
    INCOMPATIBLE = "incompatible"
