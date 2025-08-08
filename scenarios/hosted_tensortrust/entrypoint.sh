#!/usr/bin/env bash

set -e

# TODO: not checking healthcheck port for now
# parse scenarios.toml to get first launcher_port and set it to HEALTHCHECK_PORT
# export HEALTHCHECK_PORT=$(python - <<'PY'
# import tomllib, os, pathlib, sys, re, json
# data = tomllib.load(open(os.environ['SCENARIO_ROOT'] + '/scenario/scenario.toml','rb'))
# print(data['agents'][0]['launcher_port'])
# PY
# )

# in case user needs customized packages: /workspace/requirements.txt
if [ -f /workspace/requirements.txt ]; then
  pip install -r /workspace/requirements.txt
fi

# let container's 127.0.0.1:9000-9001 be accessible from host
for port in $(seq 9000 9001); do
    socat TCP-LISTEN:$port,bind=127.0.0.1,fork,reuseaddr \
          TCP:host.docker.internal:$port &
done

# load scenario
exec ab load_scenario "$SCENARIO_ROOT/scenario"
