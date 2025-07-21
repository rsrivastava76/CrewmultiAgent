# Warning control
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
from utils import get_openai_api_key
import os
import yaml
from crewai import Agent, Task, Crew
import pandas as pd

from AzureTools import ProjectSprintDataFetcherTool, WorkItemDataFetcherTool
openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

# Define file paths for YAML configurations
files = {
    'agents': 'config/Project_report_agents.yaml',
    'tasks': 'config/Project_report_tasks.yaml'
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
data_collection_agent = Agent(
  config=agents_config['data_collection_agent'],
  tools=[ProjectSprintDataFetcherTool(), WorkItemDataFetcherTool()]
)

analysis_agent = Agent(
  config=agents_config['analysis_agent']
)

# Creating Tasks
data_collection = Task(
  config=tasks_config['data_collection'],
  agent=data_collection_agent
)

data_analysis = Task(
  config=tasks_config['data_analysis'],
  agent=analysis_agent
)

# report_generation = Task(
#   config=tasks_config['report_generation'],
#   agent=analysis_agent,
# )

report_generation = Task(
  config=tasks_config['report_generation'],
  agent=analysis_agent,
  return_direct_result=True
)


# Creating Crew
crew = Crew(
  agents=[
    data_collection_agent,
    analysis_agent
  ],
  tasks=[
    data_collection,
    data_analysis,
    report_generation
  ],
  verbose=True
)

if __name__ == "__main__":
    # Kick off the crew and execute the process
    result = crew.kickoff()
    print("Type of result returned from crew.kickoff():", type(result))

    if result is None:
        print("❌ No result was returned from crew.kickoff().")
    else:
        # # Usage Metrics and Costs
        # total_tokens = crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens
        # costs = 0.150 * total_tokens / 1_000_000
        # print(f"Total tokens used: {total_tokens}")
        # print(f"Total costs: ${costs:.4f}")
        #
        # # Convert UsageMetrics instance to a DataFrame and print
        # df_usage_metrics = pd.DataFrame([crew.usage_metrics.model_dump()])
        # print("\n=== Usage Metrics ===")
        # print(df_usage_metrics.to_string(index=False))
        #result_dict = result.pydantic.model_dump()
        print("\n=== Full Result ===")
        print(result)