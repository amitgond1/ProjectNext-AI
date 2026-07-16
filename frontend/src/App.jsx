import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight, Bookmark, BrainCircuit, Check, CheckCircle2, ChevronLeft, Clock3, Code2, Copy,
  Download, FolderHeart, Layers3, LayoutGrid, Lightbulb, ListChecks, LoaderCircle,
  MessageSquareText, Rocket, Search, SlidersHorizontal, Sparkles, Star, Target,
  ThumbsDown, ThumbsUp, TrendingUp, UserRound, X,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const RESULT_CACHE_VERSION = "adaptive-preference-v4";
const initialForm = {
  name: "",
  skills: "Python, FastAPI, React",
  interests: "AI, recommendation systems, developer tools",
  career_goal: "AI_ML",
  target_companies: "Google, Microsoft, Amazon",
  project_vision: "",
  experience_summary: "",
  desired_outcome: "JOB",
  weekly_hours: 10,
  preferred_domains: "",
  excluded_technologies: "",
  must_have_technologies: "",
  difficulty: "intermediate",
  time_available_weeks: 8,
};
const presets = {
  AI_ML: { skills: "Python, FastAPI, React, PyTorch", interests: "AI, LLMs, recommendation systems", difficulty: "intermediate" },
  SDE: { skills: "JavaScript, React, Node.js, PostgreSQL", interests: "system design, developer tools, SaaS", difficulty: "intermediate" },
  DATA_SCIENCE: { skills: "Python, SQL, Pandas, Scikit-learn", interests: "predictive analytics, experimentation, machine learning", difficulty: "intermediate" },
  DATA_ENGINEERING: { skills: "Python, SQL, Apache Spark, Docker", interests: "data pipelines, lakehouse, streaming systems", difficulty: "intermediate" },
  DEVOPS: { skills: "Python, Docker, AWS, Linux", interests: "cloud, automation, observability", difficulty: "advanced" },
  CYBERSECURITY: { skills: "Python, Linux, SQL, Docker", interests: "security automation, threat detection, incident response", difficulty: "intermediate" },
  PRODUCT: { skills: "JavaScript, React, FastAPI, PostgreSQL", interests: "SaaS, product analytics, user experience", difficulty: "intermediate" },
};
const roleLabels = { AI_ML: "AI / ML Engineer", SDE: "Software Engineer", DATA_SCIENCE: "Data Scientist", DATA_ENGINEERING: "Data Engineer", DEVOPS: "DevOps / Cloud", CYBERSECURITY: "Cybersecurity", PRODUCT: "Product Engineer" };
const domainOptions = ["Data Science", "Data Engineering", "Generative AI", "Applied AI", "Developer Tools", "FinTech", "HealthTech", "Cybersecurity", "Cloud & DevOps", "E-commerce"];
const toList = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
const loadLocal = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
};

function ScoreRing({ value }) {
  const degrees = Math.max(0, Math.min(100, value)) * 3.6;
  return <div className="score-ring" style={{ background: `conic-gradient(#7155df ${degrees}deg, #e9e8ef 0deg)` }}><span>{Math.round(value)}</span></div>;
}

function BlueprintModal({ project, userId, onClose, onNotice }) {
  const [blueprint, setBlueprint] = useState(null);
  const [error, setError] = useState("");
  const progressKey = `projectnext_progress_${project.id}`;
  const [completed, setCompleted] = useState(() => loadLocal(progressKey, []));

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/projects/${project.id}/blueprint?user_id=${encodeURIComponent(userId)}`)
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "Build plan unavailable");
        if (active) setBlueprint(data);
      })
      .catch((requestError) => active && setError(requestError.message));
    return () => { active = false; };
  }, [project.id, userId]);

  useEffect(() => { localStorage.setItem(progressKey, JSON.stringify(completed)); }, [completed, progressKey]);
  useEffect(() => {
    const closeOnEscape = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  const toggleMilestone = (id) => setCompleted((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);
  const progress = blueprint ? Math.round((completed.length / blueprint.milestones.length) * 100) : 0;
  const downloadReadme = () => {
    const blob = new Blob([blueprint.readme_markdown], { type: "text/markdown" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob); link.download = `${project.slug}-README.md`; link.click();
    URL.revokeObjectURL(link.href); onNotice("README downloaded.");
  };
  const copyResume = async () => {
    await navigator.clipboard.writeText(blueprint.resume_bullets.map((item) => `• ${item}`).join("\n"));
    onNotice("Resume bullets copied.");
  };

  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className="blueprint-modal" role="dialog" aria-modal="true" aria-label={`${project.title} build plan`}>
      <header className="blueprint-header">
        <div><p className="eyebrow">Execution workspace</p><h2>{project.title}</h2><span>{project.domain} · {project.estimated_weeks} weeks · {project.difficulty}</span></div>
        <button className="modal-close" onClick={onClose} aria-label="Close"><X size={20} /></button>
      </header>
      {!blueprint && !error && <div className="blueprint-loading"><LoaderCircle className="spin" size={28} /><h3>Creating your personalized build plan</h3><p>Mapping architecture, milestones and portfolio evidence…</p></div>}
      {error && <div className="blueprint-loading error-state"><X size={28} /><h3>Could not load build plan</h3><p>{error}</p></div>}
      {blueprint && <div className="blueprint-body">
        <div className="blueprint-intro"><div><Lightbulb size={19} /><p><strong>Your differentiator</strong>{blueprint.unique_angle}</p></div>{blueprint.skill_gap.length > 0 && <div><BrainCircuit size={19} /><p><strong>Skills you will add</strong>{blueprint.skill_gap.join(" · ")}</p></div>}</div>
        <div className="plan-progress"><div><span>Build progress</span><strong>{progress}%</strong></div><div className="completion-track"><i style={{ width: `${progress}%` }} /></div></div>
        <div className="blueprint-layout">
          <div className="milestone-column">
            <div className="section-title"><ListChecks size={18} /><div><h3>Weekly execution plan</h3><p>Check milestones as you ship them</p></div></div>
            {blueprint.milestones.map((milestone) => <article className={`milestone ${completed.includes(milestone.id) ? "done" : ""}`} key={milestone.id}>
              <button className="milestone-check" onClick={() => toggleMilestone(milestone.id)}>{completed.includes(milestone.id) ? <Check size={16} /> : milestone.week_label.replace(/\D/g, "").slice(0, 2)}</button>
              <div><span>{milestone.week_label}</span><h4>{milestone.title}</h4><ul>{milestone.tasks.map((task) => <li key={task}>{task}</li>)}</ul><p><strong>Ship:</strong> {milestone.deliverable}</p></div>
            </article>)}
          </div>
          <aside className="blueprint-side">
            <div className="plan-panel"><div className="section-title"><Layers3 size={18} /><h3>Architecture</h3></div><ol>{blueprint.architecture.map((item) => <li key={item}>{item}</li>)}</ol></div>
            <div className="plan-panel"><div className="section-title"><Target size={18} /><h3>Success criteria</h3></div><ul>{blueprint.success_metrics.map((item) => <li key={item}>{item}</li>)}</ul></div>
            <div className="plan-panel"><div className="section-title"><MessageSquareText size={18} /><h3>Interview preparation</h3></div><ul>{blueprint.interview_questions.slice(0, 4).map((item) => <li key={item}>{item}</li>)}</ul></div>
          </aside>
        </div>
        <div className="career-kit"><div><p className="eyebrow">Portfolio career kit</p><h3>Turn the build into interview evidence</h3><p>Use truthful, outcome-focused resume bullets and a structured GitHub README.</p></div><button className="secondary" onClick={copyResume}><Copy size={16} />Copy resume bullets</button><button className="primary" onClick={downloadReadme}><Download size={16} />Download README</button></div>
      </div>}
    </section>
  </div>;
}

function ProjectCard({ project, rank, userId, saved, started, liked, disliked, onStatus, onNotice, onBlueprint, onPreference }) {
  const [busy, setBusy] = useState("");
  const sendFeedback = async (status, rating = null) => {
    setBusy(status);
    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, project_id: project.id, status, rating }),
      });
      if (!response.ok) throw new Error("Feedback could not be saved");
      onStatus(project, status);
      onNotice(status === "completed" ? "Project completed — great work!" : `${project.title} added to ${status === "saved" ? "saved projects" : "your roadmap"}.`);
    } catch (error) { onNotice(error.message, true); }
    finally { setBusy(""); }
  };
  const copyIdea = async () => {
    await navigator.clipboard.writeText(`${project.title}\n${project.description}\nTech: ${project.tech_stack.join(", ")}`);
    onNotice("Project brief copied to clipboard.");
  };

  return (
    <article className="project-card">
      <div className="card-topline"><span className="rank">#{rank} best match</span><span className={`difficulty ${project.difficulty}`}>{project.difficulty}</span></div>
      <div className="card-heading"><div><p className="eyebrow">{project.domain}</p><h3>{project.title}</h3></div><ScoreRing value={project.recommendation_score} /></div>
      <p className="description">{project.description}</p>
      <div className="reason"><Sparkles size={16} /><span>{project.reason}</span></div>
      <details className="ai-evidence">
        <summary><span><BrainCircuit size={14} />Why this match?</span><strong>{Math.round(project.content_score)}% semantic fit</strong></summary>
        <div className="evidence-content">
        <div className="evidence-bar"><i style={{ width: `${project.content_score}%` }} /></div>
        <p><b>{project.confidence} confidence</b> · Role {project.role_fit ? "matched" : "mismatch"} · Domain {project.domain_fit ? "matched" : "exploratory"}</p>
        {project.matched_skills.length > 0 && <p><b>You know:</b> {project.matched_skills.join(", ")}</p>}
        {project.skills_to_learn.length > 0 && <p><b>You will learn:</b> {project.skills_to_learn.join(", ")}</p>}
        </div>
      </details>
      <div className="preference-actions"><span>Teach the recommender</span><button className={liked ? "active positive" : ""} onClick={() => onPreference(project, "like")}><ThumbsUp size={14} />More like this</button><button className={disliked ? "active negative" : ""} onClick={() => onPreference(project, "dislike")}><ThumbsDown size={14} />Not for me</button></div>
      <div className="chips">{project.tech_stack.slice(0, 5).map((tech) => <span key={tech}>{tech}</span>)}</div>
      <div className="metrics">
        <div><Target size={17} /><span><strong>{Math.round(project.resume_impact_score)}</strong> resume impact</span></div>
        <div><Clock3 size={17} /><span><strong>{project.estimated_weeks}</strong> weeks</span></div>
        <div><BrainCircuit size={17} /><span><strong>{Math.round(project.content_score)}</strong> skill fit</span></div>
      </div>
      <div className="card-actions">
        <button className={`secondary ${saved ? "selected" : ""}`} disabled={!!busy} onClick={() => sendFeedback("saved")}>
          {busy === "saved" ? <LoaderCircle className="spin" size={17} /> : saved ? <Check size={17} /> : <Bookmark size={17} />}{saved ? "Saved" : "Save"}
        </button>
        <button className={`primary small ${started ? "selected" : ""}`} disabled={!!busy} onClick={() => sendFeedback("started")}>
          {started ? <Check size={17} /> : <Rocket size={17} />}{started ? "In roadmap" : "Start project"}
        </button>
        <button className="icon-button" title="Copy project brief" onClick={copyIdea}><Copy size={17} /></button>
      </div>
      <button className="blueprint-button" onClick={() => onBlueprint(project)}><ListChecks size={17} /><span><strong>Open personalized build plan</strong><small>Milestones, architecture, resume kit</small></span><ArrowRight size={17} /></button>
      <details><summary>Completed this project? Add your rating</summary><div className="rating-row">{[1, 2, 3, 4, 5].map((rating) => <button key={rating} onClick={() => sendFeedback("completed", rating)}><Star size={17} fill="currentColor" />{rating}</button>)}</div></details>
    </article>
  );
}

function OnboardingWizard({ form, update, applyPreset, submit, loading, error, step, setStep }) {
  const advance = (event) => {
    event.preventDefault();
    if (step < 3) setStep(step + 1);
    else submit(event);
  };
  return <form className="profile-panel wizard-panel" onSubmit={advance} autoComplete="off">
    <div className="wizard-top"><div><p className="eyebrow">Personalized in 3 steps</p><h2>{step === 1 ? "Choose your direction" : step === 2 ? "Show us your experience" : "Define your ideal project"}</h2></div><span className="step-count">0{step} / 03</span></div>
    <div className="stepper">{[1, 2, 3].map((item) => <button type="button" key={item} className={item <= step ? "active" : ""} onClick={() => item < step && setStep(item)}><i>{item < step ? <Check size={12} /> : item}</i><span>{item === 1 ? "Goal" : item === 2 ? "Experience" : "Preferences"}</span></button>)}</div>
    <div className="wizard-content" key={step}>
      {step === 1 && <>
        <div className="field-heading"><strong>What role are you targeting?</strong><span>Select one path to start</span></div>
        <div className="role-grid">{Object.entries(roleLabels).map(([value, label]) => <button type="button" key={value} className={form.career_goal === value ? "active" : ""} onClick={() => applyPreset(value)}><span>{value === "AI_ML" ? "AI" : value === "DATA_SCIENCE" ? "DS" : value === "DATA_ENGINEERING" ? "DE" : value.slice(0, 2)}</span><strong>{label}</strong>{form.career_goal === value && <CheckCircle2 size={16} />}</button>)}</div>
        <div className="form-grid"><label>Main outcome<select name="desired_outcome" value={form.desired_outcome} onChange={update}><option value="JOB">Get interview-ready</option><option value="SAAS">Launch a SaaS</option><option value="LEARNING">Learn a new stack</option><option value="RESEARCH">Build for research</option><option value="HACKATHON">Win a hackathon</option></select></label><label>Current level<select name="difficulty" value={form.difficulty} onChange={update}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></label></div>
        <label>Your name <span className="optional">Optional</span><input name="name" value={form.name} onChange={update} placeholder="How should we address you?" /></label>
      </>}
      {step === 2 && <>
        <div className="form-grid"><label>Your skills<input name="skills" value={form.skills} onChange={update} required placeholder="Python, React, SQL" /><small>Technologies you can use confidently</small></label><label>Your interests<input name="interests" value={form.interests} onChange={update} required placeholder="AI, fintech, developer tools" /><small>Problems and domains you enjoy</small></label></div>
        <label>Projects you have already built<textarea name="experience_summary" value={form.experience_summary} onChange={update} placeholder="MERN placement portal, FastAPI resume screener, DSA tracker" maxLength="1000" /><small>We use this to recommend a genuine next step, not another duplicate.</small></label>
        <label>Target companies or industry <span className="optional">Optional</span><input name="target_companies" value={form.target_companies} onChange={update} placeholder="Product startup, fintech, healthcare" /></label>
      </>}
      {step === 3 && <>
        <label>Describe what you want to build<textarea className="vision-input" name="project_vision" value={form.project_vision} onChange={update} placeholder="An explainable healthcare model that predicts readmission risk from tabular patient data" maxLength="500" /><small>Be specific—Sentence-BERT uses this text directly for semantic ranking.</small></label>
        <div className="form-grid"><label>Preferred domain<select name="preferred_domains" value={form.preferred_domains} onChange={update}><option value="">Let AI decide</option>{domainOptions.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label>Must-use technologies<input name="must_have_technologies" value={form.must_have_technologies} onChange={update} placeholder="FastAPI, React" /></label></div>
        <label>Technologies to avoid <span className="optional">Optional</span><input name="excluded_technologies" value={form.excluded_technologies} onChange={update} placeholder="PHP, Kafka" /></label>
        <div className="commitment-card"><div><span>Timeline</span><strong>{form.time_available_weeks} weeks</strong><input type="range" name="time_available_weeks" min="1" max="24" value={form.time_available_weeks} onChange={update} /></div><div><span>Weekly commitment</span><strong>{form.weekly_hours} hours</strong><input type="range" name="weekly_hours" min="2" max="40" value={form.weekly_hours} onChange={update} /></div></div>
      </>}
    </div>
    <div className="wizard-actions">{step > 1 && <button type="button" className="back-button" onClick={() => setStep(step - 1)}><ChevronLeft size={17} />Back</button>}<button className="primary next-button" type="submit" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={18} />Ranking your best matches…</> : step < 3 ? <>Continue<ArrowRight size={18} /></> : <><Sparkles size={18} />Generate my roadmap<ArrowRight size={18} /></>}</button></div>
    {error && <div className="error"><X size={16} />{error}</div>}
  </form>;
}

export default function App() {
  const [form, setForm] = useState(() => {
    const stored = { ...initialForm, ...loadLocal("projectnext_profile", {}) };
    if (stored.career_goal === "DATA") stored.career_goal = "DATA_SCIENCE";
    return stored;
  });
  const [recommendations, setRecommendations] = useState(() => {
    const savedProfile = loadLocal("projectnext_profile", initialForm);
    const resultRole = localStorage.getItem("projectnext_result_role");
    const cacheIsCurrent = localStorage.getItem("projectnext_result_version") === RESULT_CACHE_VERSION;
    return cacheIsCurrent && resultRole === savedProfile.career_goal ? loadLocal("projectnext_recommendations", []) : [];
  });
  const [userId, setUserId] = useState(localStorage.getItem("projectnext_user_id") || "");
  const [savedIds, setSavedIds] = useState(() => loadLocal("projectnext_saved", []));
  const [startedIds, setStartedIds] = useState(() => loadLocal("projectnext_started", []));
  const [coldStart, setColdStart] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [domain, setDomain] = useState("all");
  const [sort, setSort] = useState("match");
  const [engineInfo, setEngineInfo] = useState(() => loadLocal("projectnext_engine_info", null));
  const [blueprintProject, setBlueprintProject] = useState(null);
  const [onboardingStep, setOnboardingStep] = useState(1);
  const [likedIds, setLikedIds] = useState(() => loadLocal("projectnext_liked", []));
  const [dislikedIds, setDislikedIds] = useState(() => loadLocal("projectnext_disliked", []));

  useEffect(() => { localStorage.setItem("projectnext_profile", JSON.stringify(form)); }, [form]);
  useEffect(() => { localStorage.setItem("projectnext_saved", JSON.stringify(savedIds)); }, [savedIds]);
  useEffect(() => { localStorage.setItem("projectnext_started", JSON.stringify(startedIds)); }, [startedIds]);
  useEffect(() => { localStorage.setItem("projectnext_liked", JSON.stringify(likedIds)); }, [likedIds]);
  useEffect(() => { localStorage.setItem("projectnext_disliked", JSON.stringify(dislikedIds)); }, [dislikedIds]);

  const hasName = Boolean(form.name.trim());
  const displayName = hasName ? form.name.trim() : "Your Profile";
  const initials = form.name.trim() ? form.name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase() : null;
  const fieldsComplete = [form.skills, form.interests, form.career_goal, form.project_vision, form.difficulty, form.time_available_weeks].filter(Boolean).length;
  const completeness = Math.round((fieldsComplete / 6) * 100);
  const domains = useMemo(() => [...new Set(recommendations.map((item) => item.domain))], [recommendations]);
  const visibleProjects = useMemo(() => {
    const query = search.trim().toLowerCase();
    return recommendations
      .filter((project) => domain === "all" || project.domain === domain)
      .filter((project) => !dislikedIds.includes(project.id))
      .filter((project) => !query || `${project.title} ${project.description} ${project.tech_stack.join(" ")}`.toLowerCase().includes(query))
      .sort((a, b) => sort === "impact" ? b.resume_impact_score - a.resume_impact_score : sort === "time" ? a.estimated_weeks - b.estimated_weeks : b.recommendation_score - a.recommendation_score);
  }, [recommendations, domain, search, sort, dislikedIds]);
  const profileSummary = `${toList(form.skills).length} skills · ${roleLabels[form.career_goal]} · ${form.weekly_hours}h/week`;
  const update = ({ target }) => {
    setForm((current) => ({ ...current, [target.name]: target.value }));
    if (target.name !== "name") {
      setRecommendations([]);
      localStorage.removeItem("projectnext_recommendations");
      localStorage.removeItem("projectnext_result_role");
    }
  };
  const applyPreset = (role) => {
    setForm((current) => ({ ...current, career_goal: role, ...presets[role] }));
    setRecommendations([]);
    localStorage.removeItem("projectnext_recommendations");
    localStorage.removeItem("projectnext_result_role");
  };

  const requestRecommendations = async (payload, allowReset = true) => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 60000);
    try {
      const response = await fetch(`${API_URL}/recommend?limit=12`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: controller.signal });
      const data = await response.json().catch(() => ({}));
      if (response.status === 404 && payload.user_id && allowReset) {
        localStorage.removeItem("projectnext_user_id"); setUserId("");
        return requestRecommendations({ ...payload, user_id: null }, false);
      }
      if (!response.ok) throw new Error(data.detail || "Recommendations unavailable");
      return data;
    } finally { window.clearTimeout(timeout); }
  };

  const submit = async (event) => {
    event?.preventDefault(); setLoading(true); setError("");
    const payload = { ...form, user_id: userId || null, skills: toList(form.skills), interests: toList(form.interests), target_companies: toList(form.target_companies), preferred_domains: toList(form.preferred_domains), excluded_technologies: toList(form.excluded_technologies), must_have_technologies: toList(form.must_have_technologies), time_available_weeks: Number(form.time_available_weeks), weekly_hours: Number(form.weekly_hours), liked_project_ids: likedIds, disliked_project_ids: dislikedIds, completed_project_ids: [] };
    try {
      const data = await requestRecommendations(payload);
      setRecommendations(data.recommendations); setUserId(data.user_id); setColdStart(data.cold_start);
      const info = { engine: data.engine, interpretation: data.profile_interpreted_as, version: data.algorithm_version, signals: data.preference_signals_used };
      setEngineInfo(info); localStorage.setItem("projectnext_engine_info", JSON.stringify(info));
      localStorage.setItem("projectnext_user_id", data.user_id);
      localStorage.setItem("projectnext_recommendations", JSON.stringify(data.recommendations));
      localStorage.setItem("projectnext_result_role", form.career_goal);
      localStorage.setItem("projectnext_result_version", RESULT_CACHE_VERSION);
      requestAnimationFrame(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }));
    } catch (requestError) { setError(requestError.name === "AbortError" ? "AI engine took too long. Please try again." : requestError.message); }
    finally { setLoading(false); }
  };
  const showNotice = (message, isError = false) => { setNotice(message); if (isError) setError(message); window.setTimeout(() => setNotice(""), 3500); };
  const updateStatus = (project, status) => {
    if (status === "saved") setSavedIds((items) => [...new Set([...items, project.id])]);
    if (status === "started") { setStartedIds((items) => [...new Set([...items, project.id])]); setSavedIds((items) => [...new Set([...items, project.id])]); }
    if (status === "completed") { setStartedIds((items) => items.filter((id) => id !== project.id)); }
  };
  const updatePreference = (project, preference) => {
    if (preference === "like") {
      setLikedIds((items) => items.includes(project.id) ? items.filter((id) => id !== project.id) : [...items, project.id]);
      setDislikedIds((items) => items.filter((id) => id !== project.id));
    } else {
      setDislikedIds((items) => items.includes(project.id) ? items.filter((id) => id !== project.id) : [...items, project.id]);
      setLikedIds((items) => items.filter((id) => id !== project.id));
    }
  };

  return <main>
    <nav>
      <a className="brand" href="#top"><span><Code2 size={20} /></span> ProjectNext <em>AI</em></a>
      <div className="nav-links"><a href="#top">Discover</a><a href="#results">Recommendations</a><a href="#workspace">My workspace</a></div>
      <div className="user-chip"><span>{initials || <UserRound size={16} />}</span><div><strong>{displayName}</strong><small>{hasName ? roleLabels[form.career_goal] : "Personalized career path"}</small></div></div>
    </nav>

    <section className="hero" id="top">
      <div className="hero-copy">
        <div className="pill"><Sparkles size={14} /> For developers, graduates and career switchers</div>
        <h1>Stop building random projects. <span>Build your career.</span></h1>
        <p>Get a personalized project roadmap based on your skills, dream role, available time, and real resume impact.</p>
        <div className="hero-proof"><div><strong>233</strong><span>curated project paths</span></div><div><strong>5 phases</strong><span>from idea to deployment</span></div><div><strong>100%</strong><span>explainable matches</span></div></div>
      </div>

      <form className="profile-panel legacy-form" onSubmit={submit} autoComplete="off">
        <div className="panel-heading"><div><p className="eyebrow">Your career profile</p><h2>Tell us where you are</h2></div><span>{profileSummary}</span></div>
        <div className="completion"><div><span>Profile strength</span><strong>{completeness}%</strong></div><div className="completion-track"><i style={{ width: `${completeness}%` }} /></div></div>
        <div className="preset-row"><span>Quick start</span>{Object.keys(presets).map((role) => <button type="button" className={form.career_goal === role ? "active" : ""} key={role} onClick={() => applyPreset(role)}>{roleLabels[role]}</button>)}</div>
        <label>Your name <span className="optional">Optional</span><input name="name" value={form.name} onChange={update} autoComplete="off" placeholder="Your profile updates instantly" /></label>
        <label>Skills <input name="skills" value={form.skills} onChange={update} required /><small>Comma-separated technologies you can already use</small></label>
        <label>Interests <input name="interests" value={form.interests} onChange={update} required /></label>
        <label>What exactly do you want to build? <textarea name="project_vision" value={form.project_vision} onChange={update} placeholder="Example: I want to predict hospital readmissions using tabular patient data and build an explainable dashboard" maxLength="500" /><small>This sentence gets embedded by Sentence-BERT and directly affects ranking.</small></label>
        <label>What have you already built? <textarea name="experience_summary" value={form.experience_summary} onChange={update} placeholder="Example: MERN placement portal, FastAPI resume screener, DSA tracker" maxLength="1000" /><small>We use this to avoid repetitive ideas and recommend the next skill jump.</small></label>
        <div className="form-grid"><label>Career goal<select name="career_goal" value={form.career_goal} onChange={update}>{Object.entries(roleLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><label>Level<select name="difficulty" value={form.difficulty} onChange={update}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></label></div>
        <div className="form-grid"><label>Main outcome<select name="desired_outcome" value={form.desired_outcome} onChange={update}><option value="JOB">Get interview-ready</option><option value="SAAS">Launch a SaaS</option><option value="LEARNING">Learn a new stack</option><option value="RESEARCH">Build for research</option><option value="HACKATHON">Win a hackathon</option></select></label><label>Must-use technologies<input name="must_have_technologies" value={form.must_have_technologies} onChange={update} placeholder="FastAPI, React" /></label></div>
        <label>Target companies or industry <span className="optional">Optional</span><input name="target_companies" value={form.target_companies} onChange={update} placeholder="Google, startup, fintech, healthcare…" /></label>
        <div className="form-grid"><label>Preferred domain<select name="preferred_domains" value={form.preferred_domains} onChange={update}><option value="">Let AI decide</option>{domainOptions.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label>Avoid technologies<input name="excluded_technologies" value={form.excluded_technologies} onChange={update} placeholder="PHP, Kafka" /></label></div>
        <div className="form-grid"><label>Timeline<div className="range-line"><input type="range" name="time_available_weeks" min="1" max="24" value={form.time_available_weeks} onChange={update} /><output>{form.time_available_weeks} weeks</output></div></label><label>Weekly effort<div className="range-line"><input type="range" name="weekly_hours" min="2" max="40" value={form.weekly_hours} onChange={update} /><output>{form.weekly_hours} hours</output></div></label></div>
        <button className="primary submit" type="submit" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={19} />Analyzing skills and ranking projects…</> : <><Sparkles size={18} />Build my project roadmap<ArrowRight size={18} /></>}</button>
        {error && <div className="error"><X size={16} />{error}</div>}
      </form>
      <OnboardingWizard form={form} update={update} applyPreset={applyPreset} submit={submit} loading={loading} error={error} step={onboardingStep} setStep={setOnboardingStep} />
    </section>

    {recommendations.length > 0 && <section className="results" id="results">
      <div className="results-heading"><div><p className="eyebrow">{hasName ? `${displayName}'s` : "Your"} personalized roadmap</p><h2>Your strongest project matches</h2></div><div className="model-note"><BrainCircuit size={18} /><span>{coldStart ? "Profile + career intelligence" : "Profile + learning behavior"}</span></div></div>
      {engineInfo && <div className="engine-transparency"><div><BrainCircuit size={21} /><p><strong>How AI interpreted your request</strong><span>{engineInfo.interpretation}</span></p></div><div><span>Ranking engine</span><strong>{engineInfo.engine}</strong><small>Catalog ideas are curated. Ranking uses ML embeddings; build plans use deterministic templates.</small></div></div>}
      {(likedIds.length > 0 || dislikedIds.length > 0) && <div className="refine-banner"><div><SlidersHorizontal size={20} /><p><strong>Ready to personalize again</strong><span>{likedIds.length} liked · {dislikedIds.length} rejected. AI will move toward liked ideas and away from rejected ones.</span></p></div><button className="primary" onClick={() => submit()} disabled={loading}>{loading ? <LoaderCircle className="spin" size={17} /> : <Sparkles size={17} />}Re-rank with my feedback</button></div>}
      <div className="workspace-strip" id="workspace">
        <div><span><LayoutGrid size={18} /></span><p><strong>{recommendations.length}</strong> AI matches</p></div>
        <div><span><FolderHeart size={18} /></span><p><strong>{savedIds.length}</strong> saved</p></div>
        <div><span><Rocket size={18} /></span><p><strong>{startedIds.length}</strong> in progress</p></div>
        <div><span><TrendingUp size={18} /></span><p><strong>{Math.round(recommendations.reduce((sum, item) => sum + item.resume_impact_score, 0) / recommendations.length)}</strong> avg. impact</p></div>
      </div>
      <div className="result-tools">
        <label className="search-box"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search project or technology" /></label>
        <select value={domain} onChange={(event) => setDomain(event.target.value)}><option value="all">All domains</option>{domains.map((item) => <option key={item}>{item}</option>)}</select>
        <select value={sort} onChange={(event) => setSort(event.target.value)}><option value="match">Best match</option><option value="impact">Resume impact</option><option value="time">Fastest to build</option></select>
      </div>
      {visibleProjects.length ? <div className="project-grid">{visibleProjects.map((project, index) => <ProjectCard key={project.id} project={project} rank={index + 1} userId={userId} saved={savedIds.includes(project.id)} started={startedIds.includes(project.id)} liked={likedIds.includes(project.id)} disliked={dislikedIds.includes(project.id)} onStatus={updateStatus} onNotice={showNotice} onBlueprint={setBlueprintProject} onPreference={updatePreference} />)}</div> : <div className="no-results"><Search size={28} /><h3>No matching projects</h3><p>Try another search or domain filter.</p></div>}
    </section>}
    {blueprintProject && <BlueprintModal project={blueprintProject} userId={userId} onClose={() => setBlueprintProject(null)} onNotice={showNotice} />}
    {notice && <div className="toast"><Check size={17} />{notice}</div>}
    <footer><div className="brand"><span><Code2 size={16} /></span>ProjectNext <em>AI</em></div><p>Build proof of skill, not another tutorial clone.</p></footer>
  </main>;
}
