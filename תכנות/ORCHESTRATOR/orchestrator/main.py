import asyncio
import typer
import uvicorn
import os
import yaml
from typing import Optional

from orchestrator.core.orchestrator import Orchestrator
from orchestrator.improvement.meta_analyst import MetaAnalyst
from orchestrator.improvement.guide_writer import GuideWriter
from orchestrator.improvement.prompt_optimizer import PromptOptimizer

app = typer.Typer()
config_path = "orchestrator/config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

@app.command()
def run(task_description: str):
    """
    Execute a task using the Orchestrator.
    """
    typer.echo(f"Starting task: {task_description}")
    orchestrator = Orchestrator(config_path)
    result = asyncio.run(orchestrator.run_task(task_description))
    typer.echo("Task completed.")
    typer.echo(f"Final Output: {result.get('final_output', 'N/A')}")
    typer.echo(f"Total Cost: ${result.get('total_cost', 0.0):.4f}")
    typer.echo(f"Total Duration: {result.get('total_duration', 0.0):.2f} seconds")

@app.command()
def serve():
    """
    Start the dashboard web server.
    """
    typer.echo("Starting dashboard server...")
    os.environ["CONFIG_PATH"] = config_path # Pass config path to API
    uvicorn.run("orchestrator.api:app", host="0.0.0.0", port=8000, reload=True)

@app.command()
def optimize(agent_type: str = typer.Argument(..., help="The type of agent to optimize (e.g., planner, coder)")):
    """
    Manually trigger prompt optimization for a specific agent.
    """
    typer.echo(f"Optimizing prompt for {agent_type} agent...")
    meta_analyst = MetaAnalyst()
    prompt_optimizer = PromptOptimizer(config)
    postmortems = meta_analyst.get_recent_postmortems_for_agent(agent_type, count=20) # Get last 20 postmortems
    asyncio.run(prompt_optimizer.optimize_prompt(agent_type, postmortems))
    typer.echo(f"Prompt optimization for {agent_type} completed.")

@app.command()
def status():
    """
    Show system status and agent health.
    """
    typer.echo("System Status:")
    typer.echo(f"  Model: {config['model']}")
    typer.echo(f"  Daily Token Budget: ${config['token_budget']['daily_limit_usd']:.2f}")
    typer.echo(f"  Hard Stop Budget: ${config['token_budget']['hard_stop_usd']:.2f}")
    typer.echo("\nAgent Health (Last 10 postmortems):")
    meta_analyst = MetaAnalyst()
    agent_types = ["planner", "coder", "researcher", "qa", "communicator"]
    for agent_type in agent_types:
        failure_count = meta_analyst.get_agent_failure_count(agent_type)
        typer.echo(f"  {agent_type.capitalize()} Agent Failures: {failure_count} (out of 10 recent tasks)")
        if failure_count >= config['improvement']['guide_trigger_count']:
            typer.echo(f"    --> Recommendation: Consider generating a new guide for {agent_type}.")

@app.command()
def logs():
    """
    Display recent task postmortems.
    """
    typer.echo("Recent Task Postmortems:")
    log_path = "orchestrator/logs/task_postmortems.md"
    try:
        with open(log_path, 'r') as f:
            content = f.read()
            typer.echo(content)
    except FileNotFoundError:
        typer.echo("No postmortems found yet.")

if __name__ == "__main__":
    app()
