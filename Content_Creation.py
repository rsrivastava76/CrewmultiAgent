# Warning control
import warnings
warnings.filterwarnings('ignore')
import textwrap

import yaml

warnings.filterwarnings('ignore')
from crewai import Agent, Task, Crew
import os
from utils import get_openai_api_key,get_groq_api_key
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
from Model import ContentOutput

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

groq_api_key = get_groq_api_key()
groq_llm = "groq/llama-3.3-70b-versatile"

# Define file paths for YAML configurations
files = {
    'agents': 'config/Content_agents.yaml',
    'tasks': 'config/Content_tasks.yaml'
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
market_news_monitor_agent = Agent(
    config=agents_config['market_news_monitor_agent'],
    tools=[SerperDevTool(), ScrapeWebsiteTool()],
    #llm=groq_llm,
)

data_analyst_agent = Agent(
    config=agents_config['data_analyst_agent'],
    tools=[SerperDevTool(), WebsiteSearchTool()],
    llm=groq_llm,
)

content_creator_agent = Agent(
    config=agents_config['content_creator_agent'],
    tools=[SerperDevTool(), WebsiteSearchTool()],
)

quality_assurance_agent = Agent(
    config=agents_config['quality_assurance_agent'],
)

# Creating Tasks
monitor_financial_news_task = Task(
    config=tasks_config['monitor_financial_news'],
    agent=market_news_monitor_agent
)

analyze_market_data_task = Task(
    config=tasks_config['analyze_market_data'],
    agent=data_analyst_agent
)

create_content_task = Task(
    config=tasks_config['create_content'],
    agent=content_creator_agent,
    context=[monitor_financial_news_task, analyze_market_data_task]
)

quality_assurance_task = Task(
    config=tasks_config['quality_assurance'],
    agent=quality_assurance_agent,
    output_pydantic=ContentOutput
)

# Creating Crew
content_creation_crew = Crew(
    agents=[
        market_news_monitor_agent,
        data_analyst_agent,
        content_creator_agent,
        quality_assurance_agent
    ],
    tasks=[
        monitor_financial_news_task,
        analyze_market_data_task,
        create_content_task,
        quality_assurance_task
    ],
    verbose=True
)

if __name__ == "__main__":
    result = content_creation_crew.kickoff(inputs={
      'subject': 'Inflation in the India and the impact on the stock market in 2025-2026 financial year'
    })

    print("Type of result returned from crew.kickoff():", type(result))

    if result is None:
        print("❌ No result was returned from crew.kickoff().")
    else:
        posts = result.pydantic.model_dump()['social_media_posts']
        for post in posts:
            platform = post['platform']
            content = post['content']
            print(platform)
            wrapped_content = textwrap.fill(content, width=50)
            print(wrapped_content)
            print('-' * 50)

        print(result.pydantic.model_dump()['article'])