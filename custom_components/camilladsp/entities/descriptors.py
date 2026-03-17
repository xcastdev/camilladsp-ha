"""Entity descriptor dataclasses for CamillaDSP.

Descriptors are immutable value objects that fully describe an entity's
metadata, constraints, and mutation strategy *before* the entity is
instantiated.  The builder module produces lists of descriptors from the
normalized config document; the platform modules consume them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EntityPlatform(str, Enum):
    """HA platform that will host the entity."""

    NUMBER = "number"
    SWITCH = "switch"
    SELECT = "select"
    SENSOR = "sensor"


class MutationStrategy(str, Enum):
    """How an entity value change is propagated to the backend.

    - ``CONFIG_PATH`` – standard config document mutation via coordinator.
    - ``VOLUME_FAST`` – direct volume API bypass.
    - ``MUTE_FAST`` – direct mute API bypass.
    - ``ACTIVE_CONFIG`` – switch the active config file.
    - ``LIVE_DIAGNOSTICS`` – toggle the coordinator's live-polling mode.
    - ``READ_ONLY`` – sensors / status (no write path).
    """

    CONFIG_PATH = "config_path"
    VOLUME_FAST = "volume_fast"
    MUTE_FAST = "mute_fast"
    ACTIVE_CONFIG = "active_config"
    LIVE_DIAGNOSTICS = "live_diagnostics"
    READ_ONLY = "read_only"


class NumberMode(str, Enum):
    """Preferred UI rendering for number entities."""

    SLIDER = "slider"
    BOX = "box"
    AUTO = "auto"


class ValueOrigin(str, Enum):
    """Where the entity's value comes from."""

    LITERAL = "literal"  # normal config value
    TOKEN = "token"  # $samplerate$ etc — runtime-resolved placeholder
    RUNTIME = "runtime"  # live status / telemetry


@dataclass(frozen=True)
class EntityDescriptor:
    """Immutable specification for a single Home Assistant entity.

    Every field needed to construct and operate an entity is captured here,
    so the entity base class can be generic and descriptor-driven.

    ``unique_id`` follows the pattern
    ``camilladsp_{entry_id}_{category}_{sanitized_name}_{param_name}``.
    """

    # --- identity ---
    unique_id: str
    platform: EntityPlatform
    label: str

    # --- HA i18n / categorisation ---
    translation_key: str | None = None
    icon: str | None = None
    entity_category: str | None = None  # "config" | "diagnostic" | None
    device_class: str | None = None
    state_class: str | None = None
    native_unit: str | None = None

    # --- config linkage ---
    config_path: str | None = None  # dot/bracket path in normalized doc
    node_type: str | None = None  # filter_type, processor_type, etc.
    subtype: str | None = None  # Biquad variant, Dither type, …

    # --- value constraints ---
    value_type: type = float
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    options: list[str] | None = None

    # --- behaviour ---
    available: bool = True
    writable: bool = True
    number_mode: NumberMode = NumberMode.BOX
    value_origin: ValueOrigin = ValueOrigin.LITERAL
    mutation_strategy: MutationStrategy = MutationStrategy.CONFIG_PATH
