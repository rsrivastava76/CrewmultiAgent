# Warning control
import warnings
import pandas as pd
warnings.filterwarnings('ignore')
import os
from utils import get_openai_api_key,get_groq_api_key
from Model import ProjectPlan
from project_input import inputs
import yaml
from crewai import Agent, Task, Crew
import markdown
from datetime import datetime

openai_api_key = get_openai_api_key()
#os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4.1-mini'

groq_api_key = get_groq_api_key()
groq_llm = "groq/llama-3.3-70b-versatile"

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
  config=agents_config['project_planning_agent'],
  llm=groq_llm
)

estimation_agent = Agent(
  config=agents_config['estimation_agent'],
  llm=groq_llm
)

resource_allocation_agent = Agent(
  config=agents_config['resource_allocation_agent'],
  llm=groq_llm
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

# if __name__ == "__main__":
#     # Run the crew
#     result = crew.kickoff(inputs=inputs)
#
#     # Usage Metrics and Costs
#     total_tokens = crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens
#     costs = 0.150 * total_tokens / 1_000_000
#     print(f"Total tokens used: {total_tokens}")
#     print(f"Total costs: ${costs:.4f}")
#
#     # Convert UsageMetrics instance to a DataFrame and print
#     df_usage_metrics = pd.DataFrame([crew.usage_metrics.model_dump()])
#     print("\n=== Usage Metrics ===")
#     print(df_usage_metrics.to_string(index=False))
#
#     # Print full result dictionary
#     result_dict = result.pydantic.model_dump()
#     print("\n=== Full Result ===")
#     print(result_dict)
#
#     # Tasks DataFrame
#     tasks = result_dict.get('tasks', [])
#     if tasks:
#         df_tasks = pd.DataFrame(tasks)
#         print("\n=== Task Details ===")
#         print(df_tasks.to_string(index=False))
#     else:
#         print("\nNo task details found.")
#
#     # Milestones DataFrame
#     milestones = result_dict.get('milestones', [])
#     if milestones:
#         df_milestones = pd.DataFrame(milestones)
#         print("\n=== Milestone Details ===")
#         print(df_milestones.to_string(index=False))
#     else:
#         print("\nNo milestone details found.")


if __name__ == "__main__":
    # Run the crew
    result = crew.kickoff(inputs=inputs)

    # Usage Metrics and Costs
    total_tokens = crew.usage_metrics.prompt_tokens + crew.usage_metrics.completion_tokens
    costs = 0.150 * total_tokens / 1_000_000

    # Convert result to dictionary
    result_dict = result.pydantic.model_dump()

    # Extract tasks and milestones
    tasks = result_dict.get('tasks', [])
    milestones = result_dict.get('milestones', [])

    # Build Markdown report
    md_lines = [
        "# 🧠 CrewAI Project Report",
        f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 📌 Project Input",
        f"**Project Type:** {inputs['project_type']}",
        f"**Project Objectives:** {inputs['project_objectives']}",
        f"**Industry:** {inputs['industry']}",
        "### 👥 Team Members",
        inputs['team_members'].strip(),
        "### 📋 Project Requirements",
        inputs['project_requirements'].strip(),
        "",
        "## 📈 Usage Metrics",
        f"- Total tokens used: `{total_tokens}`",
        f"- Estimated cost: `${costs:.4f}`",
        "",
        "### 🔍 Raw Usage Metrics",
        pd.DataFrame([crew.usage_metrics.model_dump()]).to_markdown(index=False),
        ""
    ]

    if tasks:
        md_lines.append("## ✅ Tasks Breakdown")
        df_tasks = pd.DataFrame(tasks)
        md_lines.append(df_tasks.to_markdown(index=False))
    else:
        md_lines.append("No task details available.")

    if milestones:
        md_lines.append("\n## 🏁 Milestones")
        df_milestones = pd.DataFrame(milestones)
        md_lines.append(df_milestones.to_markdown(index=False))
    else:
        md_lines.append("No milestone details available.")

    # Combine markdown content
    markdown_content = "\n\n".join(md_lines)

    # Define file names
    output_folder = "crew_output"
    os.makedirs(output_folder, exist_ok=True)
    markdown_file = os.path.join(output_folder, "project_report.md")
    html_file = os.path.join(output_folder, "project_report.html")

    # Save Markdown file
    with open(markdown_file, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)

    # Convert Markdown to HTML and save
    html_body = markdown.markdown(markdown_content, extensions=['tables'])
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>CrewAI Project Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 2em; }}
            table, th, td {{ border: 1px solid #ccc; border-collapse: collapse; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
            pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Markdown report saved at: {markdown_file}")
    print(f"HTML report saved at: {html_file}")
