from crewai import Flow
from crewai.flow.flow import listen, start, and_, or_, router
from salesPipeline import lead_scoring_crew, email_writing_crew
import pandas as pd
import asyncio

class SalesPipeline(Flow):

    @start()
    def fetch_leads(self):
        # Pull our leads from the database
        # This is a mock, in a real-world scenario, this is where you would
        # fetch leads from a database
        leads = [
            {
                "lead_data": {
                    "name": "João Moura",
                    "job_title": "Director of Engineering",
                    "company": "Clearbit",
                    "email": "joao@clearbit.com",
                    "use_case": "Using AI Agent to do better data enrichment."
                },
            },
        ]
        return leads

    @listen(fetch_leads)
    def score_leads(self, leads):
        scores = lead_scoring_crew.kickoff_for_each(leads)
        self.state["score_crews_results"] = scores
        return scores

    @listen(score_leads)
    def store_leads_score(self, scores):
        # Here we would store the scores in the database
        return scores

    @listen(score_leads)
    def filter_leads(self, scores):
        return [score for score in scores if score['lead_score'].score > 70]

    @listen(and_(filter_leads, store_leads_score))
    def log_leads(self, leads):
        print(f"Leads: {leads}")

    @router(filter_leads)
    def count_leads(self, leads):
        score = leads.get("lead_score", {}).get("score", 0)
        if score > 80:
            return "high"
        elif score > 50:
            return "medium"
        else:
            return "low"

    @listen('high')
    def store_in_salesforce(self, leads):
        return leads

    @listen('medium')
    def send_to_sales_team(self, leads):
        return leads

    @listen('low')
    def write_email(self, leads):
        scored_leads = [lead.to_dict() for lead in leads]
        emails = email_writing_crew.kickoff_for_each(scored_leads)
        return emails

    @listen(write_email)
    def send_email(self, emails):
        # Here we would send the emails to the leads
        return emails

async def main():
    flow = SalesPipeline()
    flow.plot()
    emails = await flow.kickoff_async()

    # Usage metrics
    df_usage_metrics = pd.DataFrame([flow.state["score_crews_results"][0].token_usage.dict()])
    costs = 0.150 * df_usage_metrics['total_tokens'].sum() / 1_000_000
    print(f"Total costs: ${costs:.4f}")
    print(df_usage_metrics)

if __name__ == "__main__":
    asyncio.run(main())