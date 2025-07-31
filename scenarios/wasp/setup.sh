#!/bin/bash

# Setup script for WASP environment

set -e  # Exit on any error

echo "Setting up WASP environment..."

# Clone the WASP repository
[ -d "wasp" ] || git clone https://github.com/galgantar/wasp.git

# Install the WASP dependencies
cd wasp/webarena_prompt_injections/
bash setup.sh

# Prepare the authentication for the visualwebarena
cd ../visualwebarena/
source venv/bin/activate
bash prepare.sh

# TODO: Test tokenizer
# Download the ntlk punkt tokenizer
# source venv/bin/activate
# python -c "import ntlk; ntlk.download('punkt')"
