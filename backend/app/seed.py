import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Difficulty, Project


DOMAIN_PACKS = [
    ("Generative AI", ["Python", "FastAPI", "React", "PostgreSQL", "LangChain"], ["AI_ML", "SDE"], ["RAG", "evaluation", "LLM observability"]),
    ("NLP", ["Python", "FastAPI", "React", "PostgreSQL", "Transformers"], ["AI_ML", "DATA"], ["fine-tuning", "semantic search", "model serving"]),
    ("Computer Vision", ["Python", "PyTorch", "FastAPI", "React", "OpenCV"], ["AI_ML"], ["transfer learning", "inference optimization", "data pipelines"]),
    ("Recommendation Systems", ["Python", "FastAPI", "React", "PostgreSQL", "Redis"], ["AI_ML", "DATA", "SDE"], ["ranking", "embeddings", "A/B testing"]),
    ("FinTech", ["Python", "FastAPI", "React", "PostgreSQL", "Kafka"], ["SDE", "DATA"], ["event sourcing", "fraud detection", "auditability"]),
    ("HealthTech", ["Python", "FastAPI", "React", "PostgreSQL", "Docker"], ["SDE", "AI_ML"], ["privacy", "explainable ML", "monitoring"]),
    ("EdTech", ["TypeScript", "React", "FastAPI", "PostgreSQL", "Docker"], ["SDE", "PRODUCT"], ["personalization", "analytics", "accessibility"]),
    ("Developer Tools", ["TypeScript", "React", "FastAPI", "PostgreSQL", "GitHub Actions"], ["SDE", "DEVOPS"], ["static analysis", "CI/CD", "developer experience"]),
    ("Cybersecurity", ["Python", "FastAPI", "React", "PostgreSQL", "Kafka"], ["CYBERSECURITY", "SDE"], ["threat modeling", "anomaly detection", "zero trust"]),
    ("Cloud & DevOps", ["Python", "FastAPI", "React", "Docker", "Kubernetes"], ["DEVOPS", "SDE"], ["autoscaling", "observability", "infrastructure as code"]),
    ("E-commerce", ["TypeScript", "React", "FastAPI", "PostgreSQL", "Redis"], ["SDE", "PRODUCT"], ["search ranking", "caching", "payments"]),
    ("ClimateTech", ["Python", "FastAPI", "React", "PostgreSQL", "Apache Spark"], ["DATA", "AI_ML"], ["geospatial analytics", "forecasting", "data quality"]),
]

ARCHETYPES = [
    ("Intelligent Copilot", "an assistant that retrieves trusted context, takes safe actions, and evaluates every response"),
    ("Real-time Intelligence Platform", "a streaming platform that detects important events and serves low-latency insights"),
    ("Personalized Discovery Engine", "a multi-stage retrieval and ranking system with explainable recommendations"),
    ("Operations Command Center", "a role-aware dashboard for workflows, alerts, analytics, and incident response"),
    ("Predictive Decision System", "an end-to-end ML product with training, calibrated predictions, drift checks, and human review"),
    ("Collaborative Marketplace", "a trustworthy two-sided platform with search, matching, reputation, and transaction workflows"),
]

DIFFICULTY_CONFIG = {
    Difficulty.beginner: (4, 7.2, "Build an authenticated MVP with clean APIs, tests, and a measurable product outcome."),
    Difficulty.intermediate: (8, 8.5, "Add scalable data flows, background jobs, experiment tracking, and production monitoring."),
    Difficulty.advanced: (12, 9.4, "Design for multi-tenancy, high availability, model evaluation, security, and cost-aware scale."),
}

COMPANIES = ["Google", "Microsoft", "Amazon", "Meta", "Netflix", "Uber", "Atlassian", "Flipkart", "Razorpay"]

# Hand-curated flagship ideas are intentionally concrete and interview-ready.
# The generated long tail below provides coverage, while these projects should
# dominate high-quality recommendations for their matching role.
CURATED_PROJECTS = [
    {
        "title": "Customer Churn Intelligence & Retention Lab", "domain": "Data Science",
        "description": "Predict subscription churn from behavioral cohorts, explain risk with SHAP, estimate retention uplift, and serve a decision dashboard with monitored batch scoring.",
        "stack": ["Python", "Pandas", "Scikit-learn", "SHAP", "PostgreSQL", "Streamlit"], "roles": ["DATA"],
        "outcomes": ["feature engineering", "model calibration", "business experimentation"], "weeks": 7, "score": 9.5,
    },
    {
        "title": "Real-time Fraud Detection & Investigation Console", "domain": "Data Science",
        "description": "Build an imbalanced-learning fraud model, streaming feature pipeline, investigator queue, explainable alerts, and precision-recall monitoring under changing transaction patterns.",
        "stack": ["Python", "SQL", "XGBoost", "Kafka", "FastAPI", "React"], "roles": ["DATA", "AI_ML"],
        "outcomes": ["imbalanced classification", "stream processing", "cost-sensitive evaluation"], "weeks": 10, "score": 9.8,
    },
    {
        "title": "Demand Forecasting & Inventory Optimizer", "domain": "Data Science",
        "description": "Forecast SKU-level demand with backtesting, promotions and seasonality, quantify uncertainty, and recommend replenishment quantities under stockout and holding costs.",
        "stack": ["Python", "Pandas", "LightGBM", "Prophet", "PostgreSQL", "Plotly"], "roles": ["DATA"],
        "outcomes": ["time-series validation", "probabilistic forecasting", "optimization"], "weeks": 8, "score": 9.6,
    },
    {
        "title": "Product Analytics Experimentation Platform", "domain": "Data Science",
        "description": "Create event instrumentation, funnel and cohort analysis, statistically valid A/B testing, guardrail metrics, and automated experiment readouts for a SaaS product.",
        "stack": ["Python", "SQL", "dbt", "PostgreSQL", "FastAPI", "React"], "roles": ["DATA", "PRODUCT"],
        "outcomes": ["causal inference", "product metrics", "analytics engineering"], "weeks": 7, "score": 9.4,
    },
    {
        "title": "Credit Risk Scoring with Fairness Audit", "domain": "Data Science",
        "description": "Train an interpretable default-risk model, calibrate probabilities, audit subgroup fairness, simulate lending policy thresholds, and publish a model card.",
        "stack": ["Python", "Scikit-learn", "SHAP", "Fairlearn", "FastAPI", "PostgreSQL"], "roles": ["DATA", "AI_ML"],
        "outcomes": ["risk modeling", "responsible AI", "decision thresholds"], "weeks": 8, "score": 9.7,
    },
    {
        "title": "Urban Mobility Data Lakehouse", "domain": "Data Engineering",
        "description": "Ingest public transit and ride events into a medallion lakehouse, enforce data-quality contracts, build incremental models, and expose operational mobility metrics.",
        "stack": ["Python", "SQL", "Apache Spark", "Airflow", "dbt", "Docker"], "roles": ["DATA"],
        "outcomes": ["lakehouse architecture", "data quality", "orchestration"], "weeks": 10, "score": 9.5,
    },
    {
        "title": "Healthcare Readmission Risk & Care Prioritization", "domain": "Data Science",
        "description": "Predict 30-day readmission risk from longitudinal patient records, handle missing clinical data, calibrate risk, explain predictions, and design a safe care-priority workflow.",
        "stack": ["Python", "Pandas", "XGBoost", "SHAP", "FastAPI", "PostgreSQL"], "roles": ["DATA"],
        "outcomes": ["clinical ML", "missing-data strategy", "calibrated risk"], "weeks": 9, "score": 9.6,
    },
    {
        "title": "Marketing Attribution & Customer Lifetime Value", "domain": "Data Science",
        "description": "Unify campaign and purchase journeys, compare attribution models, predict customer lifetime value, segment customers, and recommend budget allocation with uncertainty.",
        "stack": ["Python", "SQL", "Pandas", "LightGBM", "dbt", "Plotly"], "roles": ["DATA"],
        "outcomes": ["customer analytics", "attribution modeling", "business storytelling"], "weeks": 7, "score": 9.3,
    },
    {
        "title": "News Trend & Market Sentiment Observatory", "domain": "Data Science",
        "description": "Collect time-stamped news, classify financial sentiment, discover emerging topics, test lead-lag relationships, and present honest backtests without look-ahead leakage.",
        "stack": ["Python", "Transformers", "Pandas", "PostgreSQL", "FastAPI", "React"], "roles": ["DATA"],
        "outcomes": ["NLP analytics", "time-series leakage", "backtesting"], "weeks": 8, "score": 9.4,
    },
    {
        "title": "Data Quality Monitoring & Lineage Hub", "domain": "Data Engineering",
        "description": "Profile warehouse tables, define freshness and validity contracts, detect schema drift, trace upstream lineage, and route actionable incidents to data owners.",
        "stack": ["Python", "SQL", "dbt", "Airflow", "PostgreSQL", "Great Expectations"], "roles": ["DATA"],
        "outcomes": ["data observability", "lineage", "pipeline reliability"], "weeks": 8, "score": 9.5,
    },
    {
        "title": "Geospatial Site Selection Decision Engine", "domain": "Data Science",
        "description": "Combine demographics, competition, mobility, and cost layers to rank new store locations, validate spatial assumptions, and explain trade-offs on an interactive map.",
        "stack": ["Python", "GeoPandas", "PostGIS", "Scikit-learn", "FastAPI", "React"], "roles": ["DATA"],
        "outcomes": ["geospatial analytics", "multi-criteria ranking", "decision support"], "weeks": 9, "score": 9.5,
    },
    {
        "title": "Semantic Job Matching & Skill Gap Engine", "domain": "Applied AI",
        "description": "Rank jobs against candidate evidence using embeddings and learning-to-rank, explain missing skills, evaluate ranking quality, and monitor bias across candidate cohorts.",
        "stack": ["Python", "Sentence-BERT", "FastAPI", "PostgreSQL", "React", "Docker"], "roles": ["AI_ML"],
        "outcomes": ["semantic retrieval", "ranking evaluation", "ML fairness"], "weeks": 9, "score": 9.7,
    },
    {
        "title": "Production RAG Evaluation Workbench", "domain": "Generative AI",
        "description": "Build hybrid retrieval, citation-grounded answers, an evaluation dataset, faithfulness and retrieval metrics, tracing, feedback capture, and cost-quality dashboards.",
        "stack": ["Python", "FastAPI", "React", "PostgreSQL", "pgvector", "OpenTelemetry"], "roles": ["AI_ML"],
        "outcomes": ["RAG evaluation", "LLM observability", "retrieval systems"], "weeks": 9, "score": 9.8,
    },
    {
        "title": "Distributed Code Review & Quality Platform", "domain": "Developer Tools",
        "description": "Analyze pull requests asynchronously, detect risky changes, manage review policies, publish GitHub checks, and design for idempotency, retries, and tenant isolation.",
        "stack": ["TypeScript", "React", "FastAPI", "PostgreSQL", "Redis", "Kafka"], "roles": ["SDE"],
        "outcomes": ["distributed systems", "API design", "developer experience"], "weeks": 10, "score": 9.7,
    },
    {
        "title": "Multi-tenant Subscription Billing System", "domain": "SaaS Engineering",
        "description": "Implement plans, metered usage, invoices, webhook idempotency, entitlements, audit logs, and failure recovery for a secure multi-tenant SaaS.",
        "stack": ["FastAPI", "React", "PostgreSQL", "Redis", "Docker", "Stripe"], "roles": ["SDE", "PRODUCT"],
        "outcomes": ["system design", "payments", "multi-tenancy"], "weeks": 9, "score": 9.6,
    },
    {
        "title": "Cloud Cost Anomaly & FinOps Platform", "domain": "Cloud & DevOps",
        "description": "Ingest cloud billing data, detect cost anomalies, allocate spend by team, forecast budgets, and trigger explainable alerts with actionable optimization recommendations.",
        "stack": ["Python", "AWS", "Terraform", "FastAPI", "PostgreSQL", "Grafana"], "roles": ["DEVOPS", "DATA"],
        "outcomes": ["FinOps", "anomaly detection", "cloud automation"], "weeks": 8, "score": 9.5,
    },
    {
        "title": "Security Event Detection & Incident Timeline", "domain": "Cybersecurity",
        "description": "Normalize authentication and network events, detect suspicious behavior, correlate alerts into incidents, and provide an analyst timeline with response playbooks.",
        "stack": ["Python", "Kafka", "OpenSearch", "FastAPI", "React", "Docker"], "roles": ["CYBERSECURITY"],
        "outcomes": ["SIEM pipelines", "threat detection", "incident response"], "weeks": 10, "score": 9.7,
    },
]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_catalog() -> list[Project]:
    projects: list[Project] = [Project(
        slug=slugify(item["title"]), title=item["title"], description=item["description"],
        tech_stack=item["stack"], domain=item["domain"], difficulty=Difficulty.intermediate,
        estimated_weeks=item["weeks"], resume_value_score=item["score"], target_roles=item["roles"],
        target_companies=COMPANIES[:4], learning_outcomes=item["outcomes"],
    ) for item in CURATED_PROJECTS]
    for domain_index, (domain, stack, roles, outcomes) in enumerate(DOMAIN_PACKS):
        for archetype_index, (archetype, concept) in enumerate(ARCHETYPES):
            for difficulty in Difficulty:
                weeks, base_score, scope = DIFFICULTY_CONFIG[difficulty]
                title = f"{domain} {archetype}"
                if difficulty != Difficulty.intermediate:
                    title = f"{title} — {difficulty.value.title()} Edition"
                score = min(10.0, base_score + ((domain_index + archetype_index) % 4) * 0.1)
                projects.append(Project(
                    slug=slugify(title),
                    title=title,
                    description=f"Create {concept} for the {domain.lower()} domain. {scope}",
                    tech_stack=stack,
                    domain=domain,
                    difficulty=difficulty,
                    estimated_weeks=weeks + (archetype_index % 3),
                    resume_value_score=score,
                    target_roles=roles,
                    target_companies=[COMPANIES[(domain_index + i) % len(COMPANIES)] for i in range(3)],
                    learning_outcomes=outcomes,
                ))
    return projects


async def seed_projects(session: AsyncSession) -> int:
    existing = set((await session.execute(select(Project.slug))).scalars())
    projects = [project for project in build_catalog() if project.slug not in existing]
    if projects:
        session.add_all(projects)
    await session.commit()
    return await session.scalar(select(func.count(Project.id))) or 0
