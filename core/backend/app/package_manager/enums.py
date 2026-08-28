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
    BLOCKED = "blocked"


class UpdateStatus(str, Enum):
    SUCCESS     = "success"
    FAILED      = "failed"
    INCOMPATIBLE = "incompatible"
    UP_TO_DATE   = "up_to_date"
    NOT_FOUND    = "not_found"


class CompatibilityLevel(str, Enum):
    COMPATIBLE   = "compatible"
    WARNING      = "warning"     # within range but close to boundary
    INCOMPATIBLE = "incompatible"
