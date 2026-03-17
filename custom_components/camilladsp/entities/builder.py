"""Descriptor builder – walks a normalized config and emits EntityDescriptors.

The top-level :func:`build_descriptors` function delegates to per-platform
factories defined in sibling modules (numbers, switches, selects, sensors).
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from ..api.models import RuntimeStatus, StoredConfig
from .descriptors import (
    EntityDescriptor,
    EntityPlatform,
    MutationStrategy,
    ValueOrigin,
)
from .numbers import build_number_descriptors
from .selects import build_select_descriptors
from .sensors import build_sensor_descriptors
from .switches import build_switch_descriptors
from .utils import is_tokenized, resolve_config_value, sanitize_id

_LOGGER = logging.getLogger(__name__)


def build_descriptors(
    config_doc: dict[str, Any],
    entry_id: str,
    stored_configs: list[StoredConfig] | None = None,
    status: RuntimeStatus | None = None,
) -> list[EntityDescriptor]:
    """Build all entity descriptors from the normalized config document.

    Parameters
    ----------
    config_doc:
        The normalized config document (see :mod:`config.schema`).
    entry_id:
        The config entry ID (used as part of unique IDs).
    stored_configs:
        Available stored config files – used for the active-config select.
    status:
        Current runtime status – used to seed sensor descriptors.

    Returns
    -------
    list[EntityDescriptor]
        A flat list of descriptors for every entity the current config
        document can expose.
    """
    descriptors: list[EntityDescriptor] = []
    descriptors.extend(build_number_descriptors(config_doc, entry_id))
    descriptors.extend(build_switch_descriptors(config_doc, entry_id))
    descriptors.extend(build_select_descriptors(config_doc, entry_id, stored_configs))
    descriptors.extend(build_sensor_descriptors(config_doc, entry_id, status))

    # Centralized token classification: convert tokenized config values
    # into read-only sensors so they are visible but not writable.
    descriptors = _classify_tokens(descriptors, config_doc)

    return descriptors


def _classify_tokens(
    descriptors: list[EntityDescriptor],
    config_doc: dict[str, Any],
) -> list[EntityDescriptor]:
    """Convert tokenized config-backed descriptors into read-only sensors.

    Walks every descriptor that has a ``config_path``.  If the backing
    value in the config document is a tokenized string (e.g.
    ``$samplerate$``), the descriptor is replaced with a read-only
    sensor so the raw token is visible but not writable.
    """
    result: list[EntityDescriptor] = []
    for desc in descriptors:
        if desc.config_path and is_tokenized(
            resolve_config_value(config_doc, desc.config_path)
        ):
            _LOGGER.debug(
                "Converting %s to read-only sensor (tokenized value)",
                desc.unique_id,
            )
            desc = replace(
                desc,
                platform=EntityPlatform.SENSOR,
                writable=False,
                value_type=str,
                value_origin=ValueOrigin.TOKEN,
                mutation_strategy=MutationStrategy.READ_ONLY,
                entity_category="diagnostic",
            )
        result.append(desc)
    return result


def diff_descriptors(
    old: list[EntityDescriptor],
    new: list[EntityDescriptor],
) -> tuple[list[EntityDescriptor], list[EntityDescriptor], list[EntityDescriptor]]:
    """Compare two descriptor sets by unique_id.

    Returns
    -------
    tuple
        ``(added, removed, unchanged)`` where each element is a list of
        :class:`EntityDescriptor`.  ``unchanged`` uses the *new* descriptor
        instances (they may carry updated options/ranges even though the ID
        is the same).
    """
    old_by_id = {d.unique_id: d for d in old}
    new_by_id = {d.unique_id: d for d in new}

    added = [d for uid, d in new_by_id.items() if uid not in old_by_id]
    removed = [d for uid, d in old_by_id.items() if uid not in new_by_id]
    unchanged = [d for uid, d in new_by_id.items() if uid in old_by_id]
    return added, removed, unchanged


__all__ = ["build_descriptors", "diff_descriptors", "sanitize_id"]
