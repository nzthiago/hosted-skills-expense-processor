#!/usr/bin/env sh

set -eu

./infra/scripts/authorize-dataverse.sh
uv run --project src --no-sync python scripts/setup_demo.py seed-policies
