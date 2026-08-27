from enum import Enum


class ModuleStatus(str, Enum):
    """
    Lifecycle states for a module as defined in the TechForge specification.

    INSTALLED    — manifest valid, structure valid, version compatible, enabled.
    DISABLED     — installed but intentionally turned off via disable() (administrative decision).
    INVALID      — manifest missing or structurally broken; cannot be loaded.
    INCOMPATIBLE — manifest is valid but platform version is outside the declared range.
    BLOCKED      — installed but a required dependency is unsatisfied (Fase 8.1 §20);
                   a technical impossibility, distinct from the administrative DISABLED.
    """
    INSTALLED    = "INSTALLED"
    DISABLED     = "DISABLED"
    INVALID      = "INVALID"
    INCOMPATIBLE = "INCOMPATIBLE"
    BLOCKED      = "BLOCKED"
