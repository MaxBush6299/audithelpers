# Squad Decisions

## Active Decisions

### 2026-03-18T17:42: Lab Structure Requirements
**By:** Max Bush (via Copilot)

**What:** Lab structure requirements for AI Calibration pipeline

**Target Audience:**
- Primary: Microsoft Solution Engineer (builds first)
- Secondary: Business auditor user (learns what they're building, how to extend)

**Approach:**
- Portal-forward (minimize CLI/Python requirements)
- Recipe-style with learning concepts embedded
- Linear sequence

**Scope:**
- Understand existing code, not build from scratch
- Portal click-through deployments (not Bicep)
- Python optional

**Lab Structure:**
- Lab 0: Deployment (security best practices, .env for secrets)
- Core Labs: Logic App pipeline
- Optional Lab: Power Apps (upload, view results, approve/reject, audit point/instruction maintenance)

**Format:**
- GitHub Pages
- Microsoft Learn style
- Duration: as long as needed

**Data:** Bring your own

**Success Criteria:**
- Running Logic App
- Given image + audit point → approval/rejection + confidence score + explanation

**Maintenance:**
- Labs used once to create system
- Auditor maintains/extends Logic App afterward

---

### 2026-03-18T17:48: Lab Design Decisions
**By:** Max Bush (via Copilot)

**Decisions:**
1. **Authentication:** Defer to post-lab hardening (out of scope for core labs)
2. **Report format:** JSON output (consumable by Power Apps/frontend)
3. **Sample data:** Bring your own only — no sanitized samples provided
4. **Azure Functions:** Use inline Logic App actions only — no Azure Functions

**Rationale for Azure Functions decision:** M's recommendation — portal-forward approach, simpler for participants, auditor maintains Logic App afterward.

**Why:** User clarifications on M's open questions

---

### 2026-03-18T17:50: Architecture Decision — No Azure Functions
**By:** Max Bush (via Copilot)

**Status:** MERGED with "Lab Design Decisions" above

**Note:** Combined into single "Lab Design Decisions" entry (2026-03-18T17:48) to avoid duplication.

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
