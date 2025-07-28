from jinja2 import Template
import toml
import argparse


def render_agent_card(template_path, output_path, **kwargs):
    with open(template_path, "r") as f:
        template = Template(f.read())

    rendered = template.render(**kwargs)

    # Verify it's valid TOML
    try:
        parsed = toml.loads(rendered)
        print(f"✓ Generated valid TOML with {len(parsed)} sections")
    except Exception as e:
        raise ValueError(f"Generated invalid TOML: {e}")

    with open(output_path, "w") as f:
        f.write(rendered)

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent-name", default="[CyberGym] Green Agent (New SDK)"
    )
    parser.add_argument("--task-id", default="arvo:368")
    parser.add_argument("--template", default="agent_card.toml.j2")
    parser.add_argument("--output", default="agent_card.toml")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8051)

    args = parser.parse_args()

    render_agent_card(
        args.template,
        args.output,
        agent_name=args.agent_name,
        task_id=args.task_id,
        host=args.host,
        port=args.port,
    )
    print(
        f"Generated {args.output} with agent_name={args.agent_name}, task_id={args.task_id}, host={args.host}, port={args.port}"
    )
