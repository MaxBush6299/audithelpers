# Routing Rules

> How work gets assigned to the team

## Domain Routing

| Signal | Route To | Notes |
|--------|----------|-------|
| Architecture, scope, decisions | M | Lead makes the call |
| Power Apps, UI, forms, user flows | Q | Frontend owns the UI |
| Python, pipeline, Azure services | Bond | Backend implementation |
| Doc Intelligence, extraction, documentation | Moneypenny | Data and docs |
| Tests, validation, edge cases | Felix | QA and testing |
| Instruction clarity, non-technical review | Vesper | User perspective |
| "Team" or multi-domain | M + relevant agents | M coordinates |

## Keyword Triggers

| Keywords | Route To |
|----------|----------|
| `power apps`, `canvas app`, `power fx`, `form`, `ui`, `frontend` | Q |
| `python`, `pipeline`, `logic app`, `function`, `azure`, `api`, `backend` | Bond |
| `doc intelligence`, `extraction`, `document`, `lab`, `instructions`, `docs` | Moneypenny |
| `test`, `pytest`, `coverage`, `edge case`, `validation` | Felix |
| `clarity`, `readable`, `user perspective`, `non-technical`, `instructions review` | Vesper |
| `architecture`, `design`, `review`, `decision`, `scope` | M |

## Review Gates

| Artifact Type | Reviewer |
|---------------|----------|
| Architecture proposals | M |
| Code changes | M (or Bond for frontend) |
| Test coverage | Felix |
| Documentation/Instructions | Vesper (clarity) + Moneypenny (accuracy) |

## Model Preferences

| Agent | Default | Bump Conditions |
|-------|---------|-----------------|
| M | auto | Premium for architecture proposals |
| Q | auto | Standard for Power Apps |
| Bond | auto | `gpt-5.2-codex` for large refactors |
| Moneypenny | auto | Haiku for docs |
| Felix | auto | Standard for test code |
| Vesper | claude-haiku-4.5 | Fast tier for review |
| Scribe | claude-haiku-4.5 | Always fast |
