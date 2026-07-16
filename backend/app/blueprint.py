from .models import Project, UserProfile


def _milestones(project: Project) -> list[dict]:
    weeks = project.estimated_weeks
    boundaries = [
        ("foundation", "Problem framing & data design", 1, max(1, round(weeks * .15))),
        ("mvp", "Working vertical slice", max(2, round(weeks * .15) + 1), max(2, round(weeks * .4))),
        ("intelligence", "Core intelligence & evaluation", max(3, round(weeks * .4) + 1), max(3, round(weeks * .65))),
        ("production", "Production engineering", max(4, round(weeks * .65) + 1), max(4, round(weeks * .85))),
        ("proof", "Portfolio proof & launch", max(5, round(weeks * .85) + 1), weeks),
    ]
    tasks = {
        "foundation": ["Interview 3 target users and write the primary job-to-be-done", "Define entities, events, API contracts, and one measurable north-star metric", "Create repository, CI checks, local Docker environment, and architecture decision record"],
        "mvp": ["Implement authentication and the smallest end-to-end user journey", f"Integrate {', '.join(project.tech_stack[:3])} into one deployable vertical slice", "Add validation, failure states, seed data, and automated API tests"],
        "intelligence": [f"Implement {project.learning_outcomes[0]} with a reproducible baseline", "Create an offline evaluation dataset and compare at least two approaches", "Expose confidence, evidence, or explanation instead of only a raw prediction"],
        "production": ["Add background processing, caching, observability, and structured logs", "Threat-model sensitive flows and test rate limits, retries, and idempotency", "Load-test the critical API and document latency/cost bottlenecks"],
        "proof": ["Deploy a live demo and record a 90-second product walkthrough", "Publish a system-design diagram, evaluation report, and engineering trade-offs", "Collect user feedback, fix the top usability issue, and write interview-ready STAR notes"],
    }
    deliverables = {
        "foundation": "Validated problem brief + architecture v1",
        "mvp": "A real user can complete the core workflow",
        "intelligence": "Evaluation report with baseline comparison",
        "production": "Monitored, tested and secure release candidate",
        "proof": "Live URL + GitHub evidence + portfolio case study",
    }
    result = []
    for key, title, start, end in boundaries:
        start, end = min(start, weeks), min(max(start, end), weeks)
        result.append({"id": key, "week_label": f"Week {start}" if start == end else f"Weeks {start}–{end}", "title": title, "tasks": tasks[key], "deliverable": deliverables[key]})
    return result


def build_blueprint(project: Project, user: UserProfile | None) -> dict:
    known = {item.casefold() for item in (user.skills if user else [])}
    gap = [item for item in project.tech_stack if item.casefold() not in known][:4]
    role = user.career_goal.replace("_", "/") if user else project.target_roles[0].replace("_", "/")
    architecture = [
        f"Experience layer — React interface for the {project.domain.lower()} workflow",
        "API layer — FastAPI validation, auth, orchestration, and versioned contracts",
        f"Intelligence layer — {', '.join(project.learning_outcomes[:2])} with offline evaluation",
        "Data layer — PostgreSQL source of truth, indexed queries, migrations, and audit history",
        "Operations layer — Docker deployment, CI/CD, metrics, traces, alerts, and backups",
    ]
    mvp = [
        "Secure onboarding and role-aware workspace",
        f"End-to-end {project.domain} core workflow using real or public data",
        "Evidence-backed output with confidence/explanation",
        "History, feedback capture, and exportable results",
        "Automated tests plus a publicly accessible deployment",
    ]
    stretch = ["Multi-tenant team workspace and RBAC", "Async event pipeline with live progress", "Experiment dashboard and model/data drift alerts", "Public API, usage limits, and billing-ready metering"]
    metrics = ["Core task success rate ≥ 85% in five usability tests", "p95 API latency < 500 ms for non-ML endpoints", "Automated test coverage ≥ 75% on critical services", "Document one domain metric and beat a simple baseline by ≥ 10%", "Zero unresolved high-severity security findings before launch"]
    bullets = [
        f"Designed and deployed a production-style {project.domain} platform using {', '.join(project.tech_stack[:4])}, delivering an explainable end-to-end workflow for {role} users.",
        f"Built and evaluated {project.learning_outcomes[0]} against a reproducible baseline, with automated quality metrics, failure analysis, and user feedback instrumentation.",
        "Engineered versioned APIs, CI/CD, structured observability, and resilient data flows; documented scalability, security, latency, and cost trade-offs.",
    ]
    questions = [
        "Why did you choose this problem, and what evidence shows users need it?",
        "Walk through the request and data flow from UI to persisted result.",
        f"How did you evaluate {project.learning_outcomes[0]}, and why is your metric appropriate?",
        "What breaks first at 100× traffic, and how would you redesign it?",
        "Describe one technical trade-off you made and the evidence behind it.",
        "How do you detect bad outputs, data drift, or silent pipeline failures?",
    ]
    milestones = _milestones(project)
    readme = f"""# {project.title}

## Problem
{project.description}

## Why this is different
This build targets a measurable {role} use case, includes evaluation and production evidence, and avoids being a tutorial clone.

## Architecture
{chr(10).join(f'- {item}' for item in architecture)}

## MVP
{chr(10).join(f'- [ ] {item}' for item in mvp)}

## Success metrics
{chr(10).join(f'- {item}' for item in metrics)}

## Tech stack
{', '.join(project.tech_stack)}

## Roadmap
{chr(10).join(f'### {item["week_label"]}: {item["title"]}{chr(10)}- [ ] {item["deliverable"]}' for item in milestones)}

## Engineering evidence
Add architecture decisions, evaluation results, load-test output, screenshots, live URL, and a 90-second demo here.
"""
    return {
        "project_id": project.id, "title": project.title,
        "problem_statement": project.description,
        "unique_angle": f"Make this portfolio-grade by validating it with real users, publishing evaluation evidence, and optimizing it for a {role} interview story.",
        "skill_gap": gap, "architecture": architecture, "mvp_features": mvp,
        "stretch_features": stretch, "success_metrics": metrics, "milestones": milestones,
        "resume_bullets": bullets, "interview_questions": questions, "readme_markdown": readme,
    }
