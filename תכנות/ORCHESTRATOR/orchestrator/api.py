from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
import asyncio
import os
import yaml
import json
from datetime import datetime

from orchestrator.core.orchestrator import Orchestrator
from orchestrator.improvement.meta_analyst import MetaAnalyst
from orchestrator.improvement.prompt_optimizer import PromptOptimizer # Import PromptOptimizer

app = FastAPI()

# Serve static files for the dashboard
# For MVP, dashboard/index.html is a single file, so we'll just return it directly
# In a more complex setup, you'd mount a StaticFiles directory
# app.mount("/static", StaticFiles(directory="orchestrator/dashboard"), name="static")

# No Jinja2Templates for MVP as it's a single HTML file with embedded JS
# templates = Jinja2Templates(directory="orchestrator/dashboard")

config_path = os.getenv("CONFIG_PATH", "orchestrator/config.yaml")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

orchestrator = Orchestrator(config_path)
meta_analyst = MetaAnalyst()
prompt_optimizer_instance = PromptOptimizer(config) # Instantiate PromptOptimizer

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serves the dashboard HTML page.
    """
    with open("orchestrator/dashboard/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/events")
async def sse_events(request: Request):
    """
    Server-Sent Events endpoint for live task status.
    """
    async def event_generator():
        while True:
            # In a real system, this would push actual task updates
            # For MVP, we'll just send dummy data or poll logs
            if await request.is_disconnected():
                break

            # Example: Send a heartbeat or dummy status
            data = {"timestamp": datetime.now().isoformat(), "message": "Dashboard heartbeat"}
            yield {"event": "message", "data": json.dumps(data)}

            # Also push recent log entries
            log_path = "orchestrator/logs/task_postmortems.md"
            try:
                with open(log_path, 'r') as f:
                    content = f.read()
                    yield {"event": "logs", "data": json.dumps({"logs": content})}
            except FileNotFoundError:
                pass # No logs yet

            await asyncio.sleep(5) # Send updates every 5 seconds
    return EventSourceResponse(event_generator())

@app.post("/run_task")
async def run_task_api(task_description: str, background_tasks: BackgroundTasks):
    """
    API endpoint to run a task.
    """
    # Run the task in a background task to not block the API
    background_tasks.add_task(orchestrator.run_task, task_description)
    return {"message": "Task started in background.", "task_description": task_description}

@app.get("/status")
async def get_status():
    """
    Returns system status and agent health.
    """
    status_info = {
        "model": config["model"],
        "daily_token_budget_usd": config["token_budget"]["daily_limit_usd"],
        "hard_stop_budget_usd": config["token_budget"]["hard_stop_usd"],
        "agent_health": {}
    }
    agent_types = ["planner", "coder", "researcher", "qa", "communicator"]
    for agent_type in agent_types:
        failure_count = meta_analyst.get_agent_failure_count(agent_type)
        status_info["agent_health"][agent_type] = {
            "failures_recent": failure_count,
            "recommendation_guide": "Consider generating new guide" if failure_count >= config['improvement']['guide_trigger_count'] else "OK"
        }
    return status_info

@app.get("/logs")
async def get_logs():
    """
    Returns recent task postmortems.
    """
    log_path = "orchestrator/logs/task_postmortems.md"
    try:
        with open(log_path, 'r') as f:
            content = f.read()
            return {"logs": content}
    except FileNotFoundError:
        return {"logs": "No postmortems found yet."}

@app.post("/optimize_prompt")
async def optimize_prompt_api(agent_type: str, background_tasks: BackgroundTasks):
    """
    API endpoint to trigger prompt optimization.
    """
    postmortems = meta_analyst.get_recent_postmortems_for_agent(agent_type, count=20)
    background_tasks.add_task(prompt_optimizer_instance.optimize_prompt, agent_type, postmortems)
    return {"message": f"Prompt optimization for {agent_type} started in background."}
