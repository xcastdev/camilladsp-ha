"""Polling strategy helpers for runtime and diagnostics refresh."""

from __future__ import annotations

from datetime import timedelta

from .api.models import GuiConfig, RuntimeStatus


def runtime_update_interval(
    default_seconds: float,
    gui_config: GuiConfig | None,
    status: RuntimeStatus | None,
    *,
    live_diagnostics: bool = False,
) -> timedelta:
    """Return the coordinator poll interval for the current runtime state.

    Fast polling is activated only when **all** of the following hold:

    1. ``live_diagnostics`` is ``True`` (the user toggled the switch).
    2. The DSP state is ``"Running"``.
    3. The backend reports a positive ``status_update_interval``.

    Otherwise the integration's default poll interval is used.
    """
    if (
        live_diagnostics
        and gui_config is not None
        and status is not None
        and status.state.strip().lower() == "running"
        and gui_config.status_update_interval > 0
    ):
        return timedelta(milliseconds=gui_config.status_update_interval)

    return timedelta(seconds=default_seconds)


def should_refresh_active_file(
    last_refresh_monotonic: float | None,
    now_monotonic: float,
    interval_seconds: float,
) -> bool:
    """Return whether the active config file should be checked now."""
    if last_refresh_monotonic is None:
        return True

    return (now_monotonic - last_refresh_monotonic) >= interval_seconds
