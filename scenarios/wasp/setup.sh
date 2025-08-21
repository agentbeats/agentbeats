#!/bin/bash

# Setup script for WASP environment

set -e  # Exit on any error

echo "Setting up WASP environment..."

# Clone the WASP repository
[ -d "wasp" ] || git clone https://github.com/galgantar/wasp.git

# Install the WASP dependencies
cd wasp/webarena_prompt_injections/
bash setup.sh

# Prepare the authentication for the visualwebarena (auto login is also done before green agent evaluator is run)
cd ../visualwebarena/
source venv/bin/activate
bash prepare.sh

# Download the nltk punkt tokenizer
source venv/bin/activate
python -c "import nltk; nltk.download('punkt')"
