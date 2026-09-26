from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.backend import windows_startup


class WindowsStartupTests(unittest.TestCase):
    def _start(self, environment):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, environment, clear=True), \
             patch.object(windows_startup, "MEDIA_ROOT", Path(directory)), \
             patch.object(windows_startup, "_backend_is_running", return_value=False), \
             patch.object(windows_startup, "_hide_console"), \
             patch.object(sys, "stdout"), patch.object(sys, "stderr"), \
             patch.object(windows_startup.uvicorn, "run") as run:
            windows_startup.main()
            return run.call_args.kwargs, os.environ.get("LUME_REMOTE_NETWORKS", "")

    def test_lumini_login_accepts_home_networks(self):
        options, networks = self._start({"LUME_MODE": "lumini"})
        self.assertEqual(options["host"], "0.0.0.0")
        self.assertEqual(networks, "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16")

    def test_login_respects_explicit_local_only_binding(self):
        options, _ = self._start({"LUME_MODE": "lumini", "LUME_BIND_HOST": "127.0.0.1"})
        self.assertEqual(options["host"], "127.0.0.1")

    def test_login_preserves_custom_networks(self):
        _, networks = self._start({"LUME_MODE": "lumini", "LUME_REMOTE_NETWORKS": "192.168.1.0/24"})
        self.assertEqual(networks, "192.168.1.0/24")
