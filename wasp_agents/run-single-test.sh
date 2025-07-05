export DATASET=webarena_prompt_injections
export REDDIT=
export GITLAB=
export OPENAI_API_KEY=


cd ../wasp/webarena_prompt_injections
source venv/bin/activate
mkdir -p testdir-with-output

# Run a single test with reduced number of tasks (config/experiment_config_reduced.raw.json)
python run.py --config configs/experiment_config_reduced.raw.json --model gpt-4o-mini --system-prompt configs/system_prompts/wa_p_som_cot_id_actree_3s.json --output-dir $(pwd)/testdir-with-output --output-format webarena --run-single
deactivate
cd ../../wasp_agents
