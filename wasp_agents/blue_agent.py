import sys
import os

# Add the visualwebarena directory to Python path before importing
visualwebarena_path = os.path.join(os.path.dirname(__file__), '..', 'wasp', 'visualwebarena')
sys.path.insert(0, visualwebarena_path)

from run import main  # type: ignore
from argparse import Namespace
import torch
from browser_env import ScriptBrowserEnv
from evaluation_harness import evaluator_router, image_utils

# Change to the visualwebarena directory before running
original_cwd = os.getcwd()
os.chdir(visualwebarena_path)

try:
    args = Namespace(render=True, slow_mo=0, action_set_tag='som', observation_type='image_som', current_viewport_only=False, viewport_width=1280, viewport_height=2048, save_trace_enabled=False, sleep_after_execution=0.0, max_steps=15, agent_type='prompt', instruction_path='../webarena_prompt_injections/configs/system_prompts/wa_p_som_cot_id_actree_3s.json', parsing_failure_th=3, repeating_action_failure_th=5, test_config_base_dir='../webarena_prompt_injections/testdir-with-output/0/webarena_tasks', eval_captioning_model_device='cpu', eval_captioning_model='Salesforce/blip2-flan-t5-xl', captioning_model='Salesforce/blip2-flan-t5-xl', provider='openai', model='gpt-4o-mini', mode='chat', temperature=1.0, top_p=0.9, context_length=0, max_tokens=384, stop_token=None, max_retry=1, max_obs_length=3840, test_start_idx=1000, test_end_idx=1004, result_dir='../webarena_prompt_injections/testdir-with-output/0/agent_logs')
    args.render_screenshot = True
    args.save_trace_enabled = True

    args.current_viewport_only = True

    # Create environment AFTER changing to visualwebarena directory
    device = torch.device("cuda") if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
   
    caption_image_fn = image_utils.get_captioning_fn(
        device, dtype, args.captioning_model
    )
    
    env = ScriptBrowserEnv(
        headless=not args.render,
        slow_mo=args.slow_mo,
        observation_type=args.observation_type,
        current_viewport_only=args.current_viewport_only,
        viewport_size={
            "width": args.viewport_width,
            "height": args.viewport_height,
        },
        save_trace_enabled=args.save_trace_enabled,
        sleep_after_execution=args.sleep_after_execution,
        # Don't pass captioning_fn here - let run.py handle it
        captioning_fn=None,
    )

    main(args, env, caption_image_fn)
    # main(args)
finally:
    # Restore original working directory
    os.chdir(original_cwd)

