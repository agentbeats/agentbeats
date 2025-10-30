import json
import random
import re
import httpx
import agentbeats as ab
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from eval_tasks import tasks, settings_list, question_requirements
from utils import run_model
from personas import benchmark_personas


CODE_DIR = Path(__file__).parent.parent
SPECIALISTS_DIR = CODE_DIR / "specialists"
QUESTIONS_DIR = CODE_DIR / "specialist_questions"
RUBRICS_DIR = CODE_DIR / "rubrics"
PROMPTS_DIR = CODE_DIR / "prompts"

full_rubrics_path = str(RUBRICS_DIR / "general")

SETTINGS_MODEL = "gpt-4o"
QUESTION_MODEL = "gpt-4o"
EXAMPLE_MODEL = "gpt-4o"
EVAL_1 = "gpt-4o"
EVAL_2 = "gpt-4o"

#########################################################
# Integrated from /personagym/code/run.py
#########################################################

# Short-listing relevant scenarios/enviornments
def select_settings(persona, settings_options):
    settings_prompt = f'''
                        Given the following persona description, select the most relevant settings from the given settings options for the persona.

                        Persona: {persona}
                        Settings: {settings_options}

                        Return ONLY the selected settings, one per line, with no other text or explanation.
                        Example output:
                        Wedding
                        Business Dinner
                        Office

                        Selected Settings:
                      '''
    selected_settings_text = run_model(input_prompt=settings_prompt, model_card=SETTINGS_MODEL)
    # Parse by splitting lines and filtering empty ones
    selected_settings = [line.strip() for line in selected_settings_text.split('\n') if line.strip()]
    return selected_settings


# Generate relevant questions given scenarios
def gen_questions(persona, settings, num_questions=1):
    questions = {task:[] for task in tasks}

    for task in tasks:
        description = question_requirements[task]
        question_prompt = f'''
                            You are tasked with determining if a person with the given persona description is able to answer questions related to {settings} that specifically test the given evaluation task.

                            Generate exactly {num_questions} challenging multi-step question(s) to do this where the questions are intended to be asked directly to the persona. You may use the question description below to guide you.

                            Persona: {persona}
                            Settings: {settings}
                            Evaluation Task: {task}
                            Questions Description: {description}

                            Return ONLY the questions, one per line, with no numbering, bullets, or other text.
                            Example output:
                            What would you do in this situation?
                            How would you handle this challenge?

                            Questions:
                      '''
        task_questions = []
        for attempt in range(5):
            try:
                task_questions_text = run_model(input_prompt=question_prompt, model_card=QUESTION_MODEL)
                # Parse by splitting lines and filtering empty ones
                parsed_questions = [line.strip() for line in task_questions_text.split('\n') if line.strip()]

                # Filter out any lines that look like headers, labels, or formatting
                parsed_questions = [q for q in parsed_questions
                                  if not q.lower().startswith('question')
                                  and not q.startswith('-')
                                  and not q.startswith('*')
                                  and not q.startswith('#')
                                  and len(q) > 10]  # Filter out very short non-questions

                if len(parsed_questions) >= num_questions:
                    task_questions = parsed_questions[:num_questions]
                    break
            except Exception as e:
                print(f"Error generating questions for {task}, attempt {attempt+1}: {e}")
                continue

        questions[task].extend(task_questions)

    return questions


def process_examples(text):
    matches = re.findall(r'Score (\d+): *Response - *"?(.*?)"?(?=\n*Score \d+: *Response -|$)', text, re.S)
    processed_text = '\n\n'.join(f'Score {score}: \"{response.strip()}\"' for score, response in matches)

    lines = processed_text.split("\n")
    filtered_lines = [line for line in lines if line.startswith("Score")]

    return "\n\n".join(filtered_lines)


def gen_score_examples(persona, qa, rubric, model):
    examples_rubric = open(PROMPTS_DIR / 'score_examples' / 'parallel_examples.txt').read()
    rubrics = []
    for question, _ in qa:
        score_prompt = open(PROMPTS_DIR / 'score_examples' / 'prompt.txt').read()
        score_prompt = score_prompt.format(persona = persona, question = question, rubric = rubric)
        rubrics.append(score_prompt)

    prompt = examples_rubric.format(rubrics=rubrics)
    examples = run_model(input_prompt=prompt, temperature=0, top_p=0, model_card=model)
    examples = process_examples(examples)
    return examples


def parse_rubric(rubric):
    match_segment = re.search(r"Therefore, the final score is\s*(\d+)", rubric)
    if match_segment:
        return int(match_segment.group(1))
    return 0


def parse_evaluation_text(evaluation_text):
    """Extract the evaluation text (explanation) before the score"""
    # Find text before "Therefore, the final score is"
    match = re.search(r"^(.*?)Therefore, the final score is", evaluation_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return evaluation_text.strip()


def format_rubrics(persona, rubric, qa):
    sys_prompt = open(PROMPTS_DIR / 'rubric_grading' / 'sys_prompt.txt').read()
    prompt_outline = open(PROMPTS_DIR / 'rubric_grading' / 'prompt.txt').read()
    rubrics = []

    examples = gen_score_examples(persona, qa, rubric, EXAMPLE_MODEL)
    for i in range(len(qa)):
        question, answer = qa[i]
        score_examples = examples[i]
        formatted_rubric = rubric.format(persona = persona, question = question, response = answer, score_example = score_examples)
        rubrics.append(formatted_rubric)

    scoring_prompt = prompt_outline.format(rubrics = rubrics)

    return sys_prompt, scoring_prompt


def parse_evaluations(text):
    pattern = r'\(\d+\) Evaluation:(.*?)(?=\(\d+\) Evaluation:|$)'
    evaluations = re.findall(pattern, text, re.DOTALL)
    evaluations = [eval.strip() for eval in evaluations]
    return evaluations


def calculate_modified_average(score_list):
    total_sum = sum(score_list)
    zero_count = score_list.count(0)
    mod_total = len(score_list) - zero_count

    return total_sum / mod_total if mod_total > 0 else total_sum


def score_rubrics(sys_prompt, scoring_prompt, num_evals=1, return_explanations=True):
    scores = []
    explanations = []

    for _ in range(num_evals):
        evaluator1 = run_model(input_prompt=scoring_prompt, temperature=0, top_p=0, model_card=EVAL_1, system = sys_prompt)
        evaluator2 = run_model(input_prompt=scoring_prompt, temperature=0, top_p=0, model_card=EVAL_2, system = sys_prompt)

        evaluator1 = parse_evaluations(evaluator1)
        evaluator2 = parse_evaluations(evaluator2)

        scores1 = [parse_rubric(rubric) for rubric in evaluator1]
        scores2 = [parse_rubric(rubric) for rubric in evaluator2]

        score1 = calculate_modified_average(scores1)
        score2 = calculate_modified_average(scores2)

        scores.append(score1)
        scores.append(score2)
        
        if return_explanations:
            # Parse evaluation explanations
            explanations1 = [parse_evaluation_text(eval_text) for eval_text in evaluator1]
            explanations2 = [parse_evaluation_text(eval_text) for eval_text in evaluator2]
            
            explanations.append({
                "evaluator1": {
                    "scores": scores1,
                    "explanations": explanations1
                },
                "evaluator2": {
                    "scores": scores2,
                    "explanations": explanations2
                }
            })
    
    if return_explanations:
        return {
            "average_score": sum(scores) / len(scores),
            "detailed_explanations": explanations
        }
    else:
        return sum(scores) / len(scores)


def score_answers(persona, task_to_qa, rubrics_path=full_rubrics_path, score_example=True, return_explanations=True):
    result = {task: {"scores": [], "reasons": []} for task in task_to_qa}
    
    for task in task_to_qa:
        # Check if there are any Q&A pairs for the task before proceeding
        if not task_to_qa[task]:
            continue

        for i in range(0, len(task_to_qa[task]), 5):
            selected_qa = task_to_qa[task][i: i + 5]
            
            # This is the key change: building the correct, full path
            rubric_file_path = f"{rubrics_path}/{task}.txt"
            print(f"DEBUG: Loading rubric from: {rubric_file_path}") # Added for debugging
            
            try:
                with open(rubric_file_path, 'r') as f:
                    rubric = f.read()
            except FileNotFoundError:
                print(f"ERROR: Rubric file not found at {rubric_file_path}. Skipping task '{task}'.")
                continue

            sys_prompt, scoring_prompt = format_rubrics(persona, rubric, selected_qa)

            if return_explanations:
                score_result = score_rubrics(sys_prompt, scoring_prompt, return_explanations=True)
                result[task]["scores"].append(score_result["average_score"])
                
                # Get all explanations from this batch
                all_explanations = []
                for eval_round in score_result["detailed_explanations"]:
                    all_explanations.extend(eval_round["evaluator1"]["explanations"])
                    all_explanations.extend(eval_round["evaluator2"]["explanations"])
                result[task]["reasons"].extend(all_explanations)
            else:
                score = score_rubrics(sys_prompt, scoring_prompt)
                result[task]["scores"].append(score)
 
    return result


def mutate_question_with_llm(persona, setting, question_template, model_card="gpt-4o-mini"):
    """
    Uses an LLM to creatively rewrite a question template to fit a specific setting.
    """
    mutation_prompt = f'''
        You are a creative assistant tasked with rewriting a question to fit a specific context.
        Your goal is to make the question more natural and engaging by weaving the setting into the question's narrative.
        In case the setting is not quite consistent with the question template, generate one question that is consistent with the setting.
        Persona to be tested: {persona}
        Setting to incorporate: {setting}
        Base Question Template: "{question_template}"

        Your output must be ONLY the single, rewritten question as a string, with no other verbose text.
        
        Rewritten Question:
      '''
    
    # Use the existing run_model utility to call the LLM
    mutated_question = run_model(input_prompt=mutation_prompt, model_card=QUESTION_MODEL)
    
    # Clean up the output to ensure it's just a single string
    return mutated_question.strip().replace('"', '')

#########################################################
# For domain-specific questions
#########################################################

class SpecialistRegistry:
    """Discovers and manages all specialist configurations."""
    def __init__(self, specialists_dir: Path):
        self.specialists = []
        self.load_specialists(specialists_dir)

    def load_specialists(self, specialists_dir: Path):
        if not specialists_dir.exists():
            print(f"WARN: Specialists directory not found at {specialists_dir}")
            return
        for file_path in specialists_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                try:
                    specialist_config = json.load(f)
                    self.specialists.append(specialist_config)
                    print(f"INFO: Registered specialist'{specialist_config.get('domain_name', 'Unnamed')}'")
                except json.JSONDecodeError as e:
                    print(f"ERROR: Could not parse {file_path}: {e}")

    def find_specialist(self, persona_text: str):
        """Checks a persona for keywords to find a matching specialist."""
        persona_lower = persona_text.lower()
        for specialist in self.specialists:
            if any(keyword in persona_lower for keyword in specialist.get("keywords", [])):
                return specialist
        return None


# Initialize registry
specialist_registry = SpecialistRegistry(SPECIALISTS_DIR)

#########################################################
# Tools called by MCP
#########################################################

@ab.tool
def get_persona_by_index(persona_index: int) -> str:
    """
    Get a specific persona from the benchmark personas list by index.

    Args:
        persona_index: Index of the persona to retrieve (0-202)

    Returns:
        Persona description string

    Raises:
        ValueError: If index is out of range
    """
    if persona_index < 0 or persona_index >= len(benchmark_personas):
        raise ValueError(f"Persona index {persona_index} out of range. Valid range: 0-{len(benchmark_personas)-1}")

    return benchmark_personas[persona_index]


@ab.tool
def get_random_persona() -> str:
    """
    Select a random persona from the benchmark personas list.

    Returns:
        Randomly selected persona description string
    """
    return random.choice(benchmark_personas)


@ab.tool
def list_available_personas(start_index: int = 0, count: int = 10) -> str:
    """
    List available personas from the benchmark list.

    Args:
        start_index: Starting index (default: 0)
        count: Number of personas to return (default: 10)

    Returns:
        JSON string with list of personas and their indices
    """
    end_index = min(start_index + count, len(benchmark_personas))
    personas_subset = [
        {"index": i, "persona": benchmark_personas[i]}
        for i in range(start_index, end_index)
    ]

    return json.dumps({
        "total_personas": len(benchmark_personas),
        "start_index": start_index,
        "count": len(personas_subset),
        "personas": personas_subset
    }, indent=2)


@ab.tool
def get_persona_from_white_agent(white_agent_url: str) -> str:
    """
    Retrieve persona description from white agent's profile endpoint.

    Args:
        white_agent_url: URL of the white agent

    Returns:
        Persona description string
    """
    client = httpx.Client(timeout=30.0)
    profile_url = f"{white_agent_url}/profile"
    response = client.get(profile_url)
    response.raise_for_status()
    profile_json = response.json()
    client.close()
    return profile_json["persona_description"]


@ab.tool
def generate_evaluation_questions(persona: str) -> str:
    """
    Generate evaluation questions based on persona and context.
    Automatically detects if specialist evaluation is needed.

    Args:
        persona: Persona description of the agent being tested

    Returns:
        JSON string of generated questions grouped by task
    """
    specialist = specialist_registry.find_specialist(persona)

    if specialist:
        # Specialist workflow
        print(f"INFO: Using specialist '{specialist['domain_name']}' evaluation")
        specialist_settings = specialist.get("settings_list", settings_list)
        selected_settings = select_settings(persona, specialist_settings)
        chosen_setting = random.choice(selected_settings) if selected_settings else "a relevant professional setting"

        questions_file_path_str = specialist.get("static_questions_file")
        questions_dict = {}

        if questions_file_path_str:
            questions_file_name = Path(questions_file_path_str).name
            questions_file_path = QUESTIONS_DIR / questions_file_name

            with open(questions_file_path, 'r') as f:
                question_templates = json.load(f)

            for task, templates in question_templates.items():
                if templates:
                    chosen_template = random.choice(templates)["template"]
                    final_question = mutate_question_with_llm(persona, chosen_setting, chosen_template)
                    questions_dict.setdefault(task,[]).append(final_question)
    else:
        # Default dynamic workflow
        print("INFO: Using general evaluation criteria")
        selected_settings = select_settings(persona, settings_list)
        questions_dict = gen_questions(persona, selected_settings, num_questions=1)

    return json.dumps(questions_dict, indent=2)


@ab.tool
def evaluate_persona_responses(persona: str, task_to_qa_json: str, specialist_name: str = None) -> str:
    """
    Evaluate white agent's responses using rubric-based scoring.

    Args:
        persona: Persona description
        task_to_qa_json: JSON string of task->[(question, answer)] mappings
        specialist_name: Optional specialist domain name for custom rubrics

    Returns:
        JSON string with scores and detailed explanations
    """
    task_to_qa = json.loads(task_to_qa_json)

    # Convert JSON format to expected format
    formatted_task_to_qa = {}
    for task_name, qa_list in task_to_qa.items():
        formatted_task_to_qa[task_name] = [(qa["question"], qa["answer"]) for qa in qa_list]

    # Determine rubrics path
    if specialist_name:
        specialist = next((s for s in specialist_registry.specialists
                        if s.get("domain_name") == specialist_name), None)
        if specialist and "rubrics_path" in specialist:
            rubrics_folder_name = Path(specialist["rubrics_path"]).name
            full_rubrics_path = str(RUBRICS_DIR / rubrics_folder_name)
        else:
            full_rubrics_path = str(RUBRICS_DIR / "general")
    else:
        full_rubrics_path = str(RUBRICS_DIR / "general")

    print(f"INFO: Using rubrics from: {full_rubrics_path}")

    scores = score_answers(persona, formatted_task_to_qa, full_rubrics_path, return_explanations=True)

    # Calculate persona score - average all batch scores for each task first
    numeric_scores = {}
    for task, data in scores.items():
        if isinstance(data, dict) and 'scores' in data and data['scores']:
            # Average all batch scores for this task
            task_avg = sum(data['scores']) / len(data['scores'])
            numeric_scores[task] = task_avg
        else:
            numeric_scores[task] = 0

    # Then average across all tasks
    persona_score = sum(numeric_scores.values()) / len(numeric_scores) if numeric_scores else 0

    result = {
        'persona_score': persona_score,
        'per_task_scores': numeric_scores,
        'detailed_scores': scores
    }

    return json.dumps(result, indent=2)
