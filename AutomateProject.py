# Warning control
import warnings
import pandas as pd
warnings.filterwarnings('ignore')
import os
from utils import get_openai_api_key
from Model import ProjectPlan
from project_input import inputs
import yaml
from crewai import Agent, Task, Crew

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

# Define file paths for YAML configurations
files = {
    'agents': 'config/agents.yaml',
    'tasks': 'config/tasks.yaml'
}

# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs['agents']
tasks_config = configs['tasks']


# Creating Agents
project_planning_agent = Agent(
  config=agents_config['project_planning_agent']
)

estimation_agent = Agent(
  config=agents_config['estimation_agent']
)

resource_allocation_agent = Agent(
  config=agents_config['resource_allocation_agent']
)

# Creating Tasks
task_breakdown = Task(
  config=tasks_config['task_breakdown'],
  agent=project_planning_agent
)

time_resource_estimation = Task(
  config=tasks_config['time_resource_estimation'],
  agent=estimation_agent
)

resource_allocation = Task(
  config=tasks_config['resource_allocation'],
  agent=resource_allocation_agent,
  output_pydantic=ProjectPlan # This is the structured output we want
)

# Creating Crew
crew = Crew(
  agents=[
    project_planning_agent,
    estimation_agent,
    resource_allocation_agent
  ],
  tasks=[
    task_breakdown,
    time_resource_estimation,
    resource_allocation
  ],
  verbose=True
)

import pandas as pd

# Assuming you have already defined `crew` and `inputs` earlier in your script

if __name__ == "__main__":
    # Run the crew
    result = crew.kickoff(inputs=inputs)

    # Usage Metrics and Costs
    total_tokens = crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens
    costs = 0.150 * total_tokens / 1_000_000
    print(f"Total tokens used: {total_tokens}")
    print(f"Total costs: ${costs:.4f}")

    # Convert UsageMetrics instance to a DataFrame and print
    df_usage_metrics = pd.DataFrame([crew.usage_metrics.model_dump()])
    print("\n=== Usage Metrics ===")
    print(df_usage_metrics.to_string(index=False))

    # Print full result dictionary
    result_dict = result.pydantic.model_dump()
    print("\n=== Full Result ===")
    print(result_dict)

    # Tasks DataFrame
    tasks = result_dict.get('tasks', [])
    if tasks:
        df_tasks = pd.DataFrame(tasks)
        print("\n=== Task Details ===")
        print(df_tasks.to_string(index=False))
    else:
        print("\nNo task details found.")

    # Milestones DataFrame
    milestones = result_dict.get('milestones', [])
    if milestones:
        df_milestones = pd.DataFrame(milestones)
        print("\n=== Milestone Details ===")
        print(df_milestones.to_string(index=False))
    else:
        print("\nNo milestone details found.")
