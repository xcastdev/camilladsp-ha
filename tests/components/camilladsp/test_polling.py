"""Tests for polling strategy helpers."""

from __future__ import annotations

from datetime import timedelta

from custom_components.camilladsp.api.models import GuiConfig, RuntimeStatus
from custom_components.camilladsp.polling import (
    runtime_update_interval,
    should_refresh_active_file,
)


class TestRuntimeUpdateInterval:
    """Dynamic poll interval selection for runtime diagnostics."""

    def test_uses_gui_interval_when_live_and_running(self):
        gui = GuiConfig(status_update_interval=200)
        status = RuntimeStatus(state="Running")

        result = runtime_update_interval(5, gui, status, live_diagnostics=True)
        assert result == timedelta(milliseconds=200)

    def test_running_match_is_case_insensitive(self):
        gui = GuiConfig(status_update_interval=150)
        status = RuntimeStatus(state=" running ")

        result = runtime_update_interval(5, gui, status, live_diagnostics=True)
        assert result == timedelta(milliseconds=150)

    def test_falls_back_when_not_running(self):
        gui = GuiConfig(status_update_interval=200)
        status = RuntimeStatus(state="Paused")

        result = runtime_update_interval(5, gui, status, live_diagnostics=True)
        assert result == timedelta(seconds=5)

    def test_falls_back_without_gui_config(self):
        status = RuntimeStatus(state="Running")

        result = runtime_update_interval(5, None, status, live_diagnostics=True)
        assert result == timedelta(seconds=5)

    def test_falls_back_for_non_positive_gui_interval(self):
        gui = GuiConfig(status_update_interval=0)
        status = RuntimeStatus(state="Running")

        result = runtime_update_interval(5, gui, status, live_diagnostics=True)
        assert result == timedelta(seconds=5)

    def test_falls_back_when_live_diagnostics_off(self):
        """Fast polling requires the live_diagnostics switch to be on."""
        gui = GuiConfig(status_update_interval=200)
        status = RuntimeStatus(state="Running")

        result = runtime_update_interval(5, gui, status, live_diagnostics=False)
        assert result == timedelta(seconds=5)

    def test_default_live_diagnostics_is_false(self):
        """Without the kwarg, live_diagnostics defaults to False (slow)."""
        gui = GuiConfig(status_update_interval=200)
        status = RuntimeStatus(state="Running")

        result = runtime_update_interval(5, gui, status)
        assert result == timedelta(seconds=5)


class TestShouldRefreshActiveFile:
    """Active config file refresh throttling."""

    def test_refreshes_when_never_checked(self):
        assert should_refresh_active_file(None, 10.0, 5.0) is True

    def test_refreshes_when_interval_elapsed(self):
        assert should_refresh_active_file(10.0, 15.0, 5.0) is True

    def test_skips_when_interval_not_elapsed(self):
        assert should_refresh_active_file(10.0, 14.9, 5.0) is False
