#!/usr/bin/env bash

set -e

# parse scenarios.toml to get first launcher_port and set it to HEALTHCHECK_PORT
export HEALTHCHECK_PORT=$(python - <<'PY'
import tomllib, os, pathlib, sys, re, json
data = tomllib.load(open(os.environ['SCENARIO_ROOT'] + '/scenarios.toml','rb'))
print(data['agents'][0]['launcher_port'])
PY
)

# in case user needs customized packages: /workspace/requirements.txt
if [ -f /workspace/requirements.txt ]; then
  pip install -r /workspace/requirements.txt
fi

# load scenario
exec ab load_scenario "$SCENARIO_ROOT"
