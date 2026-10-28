#!/usr/bin/env python3
"""Standalone entry point for the CloudHeal Kubernetes E2E lifecycle check."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "control-plane" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cloudheal_control_plane.kubernetes_e2e import main

if __name__ == "__main__":
    raise SystemExit(main())
