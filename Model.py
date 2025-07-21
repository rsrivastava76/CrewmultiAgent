from typing import List
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # Only needed if you want to add config options

class TaskEstimate(BaseModel):
    task_name: str = Field(..., description="Name of the task")
    estimated_time_hours: float = Field(..., description="Estimated time to complete the task in hours")
    required_resources: List[str] = Field(..., description="List of resources required to complete the task")

    # Optional: Replace old-style class Config with this
    model_config = ConfigDict(extra="forbid")  # or other options like populate_by_name, etc.

class Milestone(BaseModel):
    milestone_name: str = Field(..., description="Name of the milestone")
    tasks: List[str] = Field(..., description="List of task IDs associated with this milestone")

    model_config = ConfigDict(extra="forbid")

class ProjectPlan(BaseModel):
    tasks: List[TaskEstimate] = Field(..., description="List of tasks with their estimates")
    milestones: List[Milestone] = Field(..., description="List of project milestones")

    model_config = ConfigDict(extra="forbid")
