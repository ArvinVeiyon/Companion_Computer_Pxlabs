#!/usr/bin/env bash
# Recreate the Python environment for the DroneCAN flashing tools.
# The venv is gitignored, so run this after a fresh clone.
#
# Deliberately a venv and NOT system python: ROS 2 uses the system interpreter.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 -m venv "$HERE/venv"
"$HERE/venv/bin/pip" install --quiet --upgrade pip
"$HERE/venv/bin/pip" install --quiet dronecan python-can

"$HERE/venv/bin/python" - <<'PY'
import can, dronecan
print("dronecan", dronecan.__version__, "| python-can", can.__version__)
PY

echo "OK. can-utils is also required:  sudo apt-get install -y can-utils"
