from crewai_tools import BaseTool
import requests
import os
import json

class ProjectSprintDataFetcherTool(BaseTool):
    name: str = "Azure DevOps Sprint Fetcher"
    description: str = "Fetches all sprint (iteration) data for a project."

    organization: str = os.environ['AZDO_ORG']
    project: str = os.environ['AZDO_PROJECT']
    team: str = os.environ['AZDO_TEAM']
    personal_access_token: str = os.environ['AZDO_PAT']

    def _run(self) -> dict:
        team = self.team

        print("Ritesh Team Name is == ", team)
        url = f"https://dev.azure.com/{self.organization}/{self.project}/{team}/_apis/work/teamsettings/iterations?api-version=7.0"

        response = requests.get(
            url,
            auth=("", self.personal_access_token)
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to fetch sprint data from Azure DevOps."}

class WorkItemDataFetcherTool(BaseTool):
    name: str = "Azure DevOps Work Item Fetcher"
    description: str = "Fetches stories, bugs, and tasks from a sprint."

    organization: str = os.environ['AZDO_ORG']
    project: str = os.environ['AZDO_PROJECT']
    personal_access_token: str = os.environ['AZDO_PAT']
    team: str = os.environ['AZDO_TEAM']
    iteration_path: str = os.environ['ITR_PATH']

    def _run(self) -> dict:
        iteration_path = self.iteration_path

        query = f"""
        SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
        FROM WorkItems
        WHERE [System.IterationPath] = '{iteration_path}'
        AND [System.WorkItemType] IN ('User Story', 'Task', 'Bug')
        ORDER BY [System.ChangedDate] DESC
        """

        print("Ritesh query ==", query)

        wiql_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit/wiql?api-version=7.0"
        response = requests.post(
            wiql_url,
            auth=("", self.personal_access_token),
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": query})
        )

        if response.status_code != 200:
            return {"error": "WIQL query failed.", "details": response.text}

        ids = [item['id'] for item in response.json().get('workItems', [])]
        if not ids:
            return {"message": "No work items found."}

        # Fetch work item details
        batch_url = f"https://dev.azure.com/{self.organization}/_apis/wit/workitemsbatch?api-version=7.0"
        batch_query = {
            "ids": ids[:200],
            "fields": [
                "System.Id", "System.Title", "System.State",
                "System.AssignedTo", "System.IterationPath",
                "System.WorkItemType", "System.Parent"
            ]
        }

        detail_response = requests.post(
            batch_url,
            auth=("", self.personal_access_token),
            headers={"Content-Type": "application/json"},
            data=json.dumps(batch_query)
        )

        if detail_response.status_code == 200:
            return detail_response.json()
        else:
            return {"error": "Failed to fetch detailed data.", "details": detail_response.text}

class StoryDataFetcherTool(BaseTool):
    name: str = "Azure DevOps Story Fetcher"
    description: str = "Fetches all User Story items from a project (optionally filtered by iteration path)."

    organization: str = os.environ['AZDO_ORG']
    project: str = os.environ['AZDO_PROJECT']
    personal_access_token: str = os.environ['AZDO_PAT']

    def _run(self, iteration_path: str = None) -> dict:
        wiql_query = "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'"
        if iteration_path:
            wiql_query += f" AND [System.IterationPath] = '{iteration_path}'"

    # def _run(self, iteration_path: str = None) -> dict:
    #     wiql_query = "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'"
    #     if iteration_path:
    #         wiql_query += f" AND [System.IterationPath] = '{iteration_path}'"
        wiql_query += " ORDER BY [System.ChangedDate] DESC"

        print("wiql_query ==" , wiql_query)

        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit/wiql?api-version=7.0"
        response = requests.post(
            url,
            auth=("", self.personal_access_token),
            headers={"Content-Type": "application/json"},
            data=json.dumps({"query": wiql_query})
        )

        if response.status_code != 200:
            return {"error": "Failed to execute WIQL query."}

        work_items_info = response.json()
        ids = [item['id'] for item in work_items_info.get('workItems', [])]

        if not ids:
            return {"message": "No user stories found."}

        batch_url = f"https://dev.azure.com/{self.organization}/_apis/wit/workitemsbatch?api-version=7.0"
        batch_query = {
            "ids": ids[:200],  # up to 200 per batch
            "fields": [
                "System.Id",
                "System.Title",
                "System.State",
                "System.AssignedTo",
                "System.IterationPath"
            ]
        }

        batch_response = requests.post(
            batch_url,
            auth=("", self.personal_access_token),
            headers={"Content-Type": "application/json"},
            data=json.dumps(batch_query)
        )

        if batch_response.status_code == 200:
            return batch_response.json()
        else:
            return {"error": "Failed to fetch user story details."}


# team_name = 'H-2'
# iteration_path = 'H-2\\Sprint 1'
#
# print("Testing ProjectSprintDataFetcherTool...")
# sprint_tool = ProjectSprintDataFetcherTool()
# # sprint_response = sprint_tool._run()
# sprint_response = sprint_tool._run(team_name=team_name)
#
# if 'error' in sprint_response:
#     print("❌ Sprint Fetch Failed:", sprint_response['error'])
# else:
#     print(f"✅ Fetched {len(sprint_response.get('value', []))} sprints.")
#     for sprint in sprint_response.get('value', []):
#         print(" -", sprint['name'], "| Start:", sprint.get('attributes', {}).get('startDate'))
#
# # Test Story Fetcher
# print("\n Testing StoryDataFetcherTool...")
# story_tool = WorkItemDataFetcherTool()
#
# # Optional: use an iterationPath from the fetched sprints (format: "Project\\Sprint Name")
# #iteration_path = None  # e.g., "MyProject\\Sprint 1"
# story_response = story_tool._run(iteration_path=iteration_path)
#
# if 'error' in story_response:
#     print("❌ Story Fetch Failed:", story_response['error'])
# else:
#     print(f"✅ Fetched {len(story_response.get('value', []))} user stories.")
#     for story in story_response.get('value', []):
#         fields = story.get('fields', {})
#         print(" -", fields.get('System.Title'), "| State:", fields.get('System.State'))
