# Lab 5: Create the Logic App

**Estimated duration:** 25 minutes  
**Owner:** Bond  
**Objective:** Create an Azure Logic App (Consumption tier) and explore the Designer interface to prepare for building the audit pipeline workflow.

---

## What You'll Learn

In this lab, you will:

- ✅ Understand what Logic Apps are and why we're using them for workflow automation
- ✅ Understand Standard vs. Consumption tiers and why we chose Consumption
- ✅ Create a Consumption-tier Logic App with naming conventions
- ✅ Navigate the Logic App Designer interface (triggers, actions, connectors, code view)
- ✅ Understand connectors and the pre-built integrations we'll use (Blob Storage, HTTP, Data Operations)
- ✅ Leave the workflow blank for now — we'll add the trigger in Lab 6

> **📝 Note:** This lab creates the Logic App framework only. In Lab 6+, you'll add triggers and actions to build the complete audit pipeline.

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 4 complete:** Azure Blob Storage account created with `audit-input` and `audit-output` containers
- ✅ **Resource Group from Lab 0:** You know your Resource Group name (e.g., `rg-audit-pipeline-{your-initials}`)
- ✅ **Azure subscription** with **Logic App Contributor** or **Contributor** role at the Resource Group level
- ✅ **Initials ready:** For the Logic App naming convention

---

## What Is Azure Logic Apps?

**Logic Apps** is a cloud-based workflow automation service that lets you build complex integrations using a visual interface. Instead of writing code, you design workflows using:

- **Triggers** — Events that start your workflow (e.g., "When a blob is uploaded")
- **Actions** — Tasks that run in response (e.g., "Call Azure OpenAI API")
- **Connectors** — Pre-built integrations to Azure services, Microsoft 365, and 3rd-party APIs
- **Control logic** — Conditions, loops, and error handling

**Why Logic Apps for this project?**
- **Portal-forward:** Build workflows entirely in the Azure Portal — no coding required
- **Audit-pipeline-ready:** Connectors for Blob Storage (triggers), HTTP (API calls), and Data Operations (JSON parsing)
- **Serverless:** Pay per execution — no VMs or servers to manage
- **Integrations:** Native support for Document Intelligence, Azure OpenAI, and other Azure services

### Consumption vs. Standard Tier

Azure Logic Apps offers two deployment options:

| Feature | Consumption | Standard |
|---|---|---|
| **Pricing** | Pay-per-execution (metered billing) | Per-hour (fixed monthly cost) |
| **Triggers** | Built-in connectors only | Built-in + managed connectors |
| **Connectors** | ~400+ managed connectors | ~400+ managed connectors |
| **Performance** | Milliseconds to seconds | Ultra-low latency (microseconds) |
| **Use Case** | Learning, testing, variable workloads | Production, high-volume, consistent workloads |
| **Best For** | This lab! | Enterprise pipelines |

**We're using Consumption because:**
- Cost-effective for learning (you only pay when workflows execute)
- Simpler management (less infrastructure to maintain)
- Perfect for auditors who'll extend/maintain the Logic App afterward
- All connectors we need are available

---

## What Are Connectors?

**Connectors** are pre-built integrations that Logic App uses to communicate with other services. Think of them as bridges:

```
Logic App → [Connector] → External Service
```

**Connectors we'll use in this pipeline:**

| Connector | Purpose | Role in Pipeline |
|---|---|---|
| **Azure Blob Storage** | Monitor file uploads and write results | **Trigger:** Watch `audit-input` container; **Action:** Write JSON to `audit-output` |
| **HTTP** | Call external APIs | **Action:** Call Document Intelligence and Azure OpenAI endpoints |
| **Data Operations** | Transform and parse data | **Action:** Parse JSON responses, compose outputs |

Each connector has **actions** (what it can do) and sometimes **triggers** (events it can detect).

---

## Step 1: Navigate to Create a Logic App

### 1.1 Open Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure account

### 1.2 Start Logic App Creation

1. In the search bar at the top, type **logic app** and select **Logic Apps**
2. Click **+ Create** (or **Create logic app** if visible)
3. This opens the "Create Logic App" page

---

## Step 2: Configure Logic App Settings

### 2.1 Basics Tab

Fill in the following details:

1. **Subscription:** Select your Azure subscription

2. **Resource group:** Select the Resource Group from Lab 0 (e.g., `rg-audit-pipeline-js`)

3. **Logic App name:** Use this naming convention:
   - Format: `logic-audit-pipeline-{your-initials}`
   - Example: If your initials are JS, use `logic-audit-pipeline-js`
   - **Important:** Use lowercase, hyphens OK (unlike Storage Account names)

   > **💡 Tip:** Choose a name that's descriptive and easy to reference in documentation and logs.

4. **Region:** Select the same region as your Resource Group from Lab 0 (e.g., **East US 2**)

   > **⚠️ Important:** Keeping all resources in the same region reduces latency and ensures regional compliance.

5. **Plan:** Select **Consumption**
   - ✅ This is the default and recommended tier for this lab
   - If you see "Logic App (Consumption)" as an option, select that

   > **💡 Note:** If "Standard" appears as an option, do NOT select it. Standard is for production high-volume pipelines and incurs fixed hourly costs.

6. **Enable log analytics:** Leave **Off** (optional for labs; turn on in production for debugging)

### 2.2 Review Your Settings

Before proceeding, verify:

- Logic App name: `logic-audit-pipeline-{initials}` ✓
- Subscription: Correct ✓
- Resource Group: Same as Lab 0 ✓
- Region: Same as other resources ✓
- Plan: **Consumption** ✓

---

## Step 3: Review and Create

1. Click **Review + Create** at the bottom
2. Azure will validate your settings. You should see ✅ (green check) for all fields
3. Click **Create**

Wait for the deployment to complete (~1-2 minutes). You'll see **"Deployment succeeded"** when done.

> **💡 Tip:** While waiting, take a moment to understand the **Connectors** section above. You'll be using these in Labs 6-8.

---

## Step 4: Open the Logic App Designer

Once deployment is complete, you'll be taken to the Logic App overview.

### 4.1 Access the Designer

1. Click **Go to resource** (if prompted)
   - Or: In the search bar, search for your Logic App name (e.g., `logic-audit-pipeline-js`)
   - Click on your Logic App in the results

2. You should now see your Logic App's **Overview** page

3. Look for the **Logic App Designer** — there are two ways to access it:
   - **Blank canvas:** Click **Blank Logic App** (if you see it on the Overview)
   - **Via menu:** In the left menu, click **Logic app designer**

The Designer should open, showing a blank canvas.

---

## Step 5: Tour the Designer Interface

The Logic App Designer is divided into several key areas. Let's explore each one.

### 5.1 The Workflow Canvas (Center)

```
+----------+
|  START   |  ← This is where triggers go
+----------+
     ↓
[Your actions go here]
     ↓
+----------+
|   END    |  ← This is implicit; no endpoint needed
+----------+
```

**The canvas** is where you:
- Add triggers (what starts the workflow)
- Add actions (what happens in sequence)
- Add conditions, loops, and error handling

### 5.2 Search Bar (Top Left)

At the top of the Designer, you'll see a search box labeled **Search connectors and triggers**.

**Use this to:**
- Search for "Blob Storage" to find blob triggers/actions
- Search for "HTTP" to find HTTP action
- Search for "Parse JSON" for data transformation

> **💡 Tip:** Connectors appear as cards in the search results. Click on one to see all available triggers and actions.

### 5.3 The Trigger Step

The first step in any Logic App workflow is a **trigger** — an event that starts execution:

```
[Trigger icon] Choose a trigger
```

Common triggers in our pipeline:
- **Blob Storage trigger:** "When a blob is created" (we'll use this in Lab 6)
- **HTTP trigger:** "When an HTTP request is received"
- **Recurrence trigger:** "Run on a schedule"

For now, **leave this blank** — we'll add the blob trigger in Lab 6.

### 5.4 Adding Actions

Once you have a trigger, you can add actions by clicking **+ New step**:

```
[Trigger]
   ↓
[+ New step]  ← Click here
   ↓
[Search for action or connector]
   ↓
[Action executes]
```

Actions execute **in order**, top to bottom. Each action's output can be used as input to the next action.

### 5.5 Code View

At the top right, you'll see a **Code view** button (looks like `{ }`). Click it to see the workflow in JSON:

```json
{
  "triggers": {},
  "actions": {}
}
```

- **Blank now:** Because we haven't added any triggers/actions yet
- **Useful for:** Advanced debugging, understanding workflow structure, importing/exporting workflows
- **We'll use it:** In Labs 6-8 to verify our workflow is correct before testing

### 5.6 Save Button

At the top, you'll see a **Save** button. Click it to save your workflow after making changes.

> **⚠️ Important:** Always save your changes! An unsaved workflow will lose its changes if you navigate away.

---

## Step 6: Understand the Workflow Anatomy

Our complete audit pipeline will look like this (preview for Labs 6+):

```
┌─ Trigger ─────────────────────────────────┐
│ When a blob is created                     │
│ (in audit-input container)                │
└───────────────────────────────────────────┘
         ↓
┌─ Action 1 ────────────────────────────────┐
│ Analyze Image                              │
│ (HTTP POST to Document Intelligence)      │
└───────────────────────────────────────────┘
         ↓
┌─ Action 2 ────────────────────────────────┐
│ Call OpenAI API                            │
│ (HTTP POST with extracted text)           │
└───────────────────────────────────────────┘
         ↓
┌─ Action 3 ────────────────────────────────┐
│ Parse JSON Response                        │
│ (Compose structured result)                │
└───────────────────────────────────────────┘
         ↓
┌─ Action 4 ────────────────────────────────┐
│ Write Results                              │
│ (Create blob in audit-output)             │
└───────────────────────────────────────────┘
```

Each step:
- Takes input from previous steps (or the trigger)
- Processes the data
- Passes output to the next step
- If any step fails, you can add error handling

---

## Step 7: Explore Connectors in the Designer

Let's get familiar with the connectors you'll use. **Don't add them yet** — just explore:

### 7.1 Search for Blob Storage Connector

1. In the Designer, click the search box (top left)
2. Type **blob storage** and press Enter
3. You'll see **"Azure Blob Storage"** as a result
4. Click on it to see available triggers and actions:
   - **Triggers:** "When a blob is created", "When a blob is updated"
   - **Actions:** "Create blob", "List blobs", "Get blob content", "Delete blob"

> **💡 Note:** We'll use "When a blob is created" as our trigger in Lab 6.

### 7.2 Search for HTTP Connector

1. Clear the search box
2. Type **http** and press Enter
3. You'll see **"HTTP"** as a result
4. Click on it to see available actions:
   - **"HTTP"** — Send HTTP requests (GET, POST, PUT, DELETE)

> **💡 Note:** We'll use this to call Document Intelligence and Azure OpenAI APIs in Labs 6-7.

### 7.3 Search for Data Operations Connector

1. Clear the search box
2. Type **data operations** and press Enter
3. You'll see **"Data Operations"** as a result
4. Click on it to see available actions:
   - **"Compose"** — Create a JSON object or string
   - **"Parse JSON"** — Parse JSON responses into structured fields
   - **"Filter array"**, **"Select"**, **"Join"** — Array operations

> **💡 Note:** We'll use "Compose" and "Parse JSON" to structure our results in Labs 7-8.

**After exploring, close the search results** by clicking elsewhere or pressing Escape. Your workflow canvas should still be blank.

---

## Step 8: Verify Your Setup

Use this checklist to confirm your Logic App is ready:

- ✅ **Logic App created:** `logic-audit-pipeline-{initials}` exists in Azure Portal
- ✅ **Correct tier:** Consumption (not Standard)
- ✅ **Same Resource Group:** Matches Lab 0
- ✅ **Same region:** Matches other resources
- ✅ **Designer opens:** You can see the blank canvas
- ✅ **Connectors searchable:** Blob Storage, HTTP, Data Operations all appear in search
- ✅ **Code view accessible:** The `{ }` button at top right works

If all items are checked, your Logic App is ready for Lab 6.

---

## Understanding the Workflow State

Your Logic App Designer is now **blank and saved**. This means:

- **Trigger:** Not yet defined — the workflow won't start automatically
- **Actions:** None — nothing happens if the workflow starts
- **Status:** ✅ Ready for configuration (Labs 6+)

**What's next?**
- **Lab 6:** Add the Blob Storage trigger ("When a blob is created")
- **Lab 7:** Add HTTP action to call Document Intelligence
- **Lab 8:** Add HTTP action to call Azure OpenAI
- **Lab 9+:** Add data transformation, error handling, and result output

---

## Key Concepts

### Triggers vs. Actions

- **Trigger:** Starts the workflow automatically when an event occurs
  - Example: "When a blob is uploaded to audit-input"
  - Every workflow needs at least one trigger
  - Triggers check for events on a schedule (every few minutes for blobs)

- **Action:** Tasks that run after the trigger
  - Example: "Call Document Intelligence API"
  - Actions execute in sequence
  - Each action's output feeds into the next action

### Connectors

**Connectors** are reusable integrations:
- **Built-in connectors:** Azure services (Blob Storage, HTTP, Data Operations)
- **Managed connectors:** 3rd-party integrations (Salesforce, Slack, GitHub)
- **Enterprise connectors:** Advanced security and compliance features

All connectors we need are **built-in** — no extra licensing required.

### Consumption Pricing Model

Logic App Consumption pricing is based on:
- **Trigger executions:** Each time the trigger fires
- **Action executions:** Each action that runs
- **API connections:** Some connectors incur per-call costs

Example pricing (approximate):
- 100 executions/month = ~$0.50
- 10,000 executions/month = ~$5-$10

For this lab, cost will be **near zero** until you start uploading images in Labs 10+.

### Stateless vs. Stateful Workflows

- **Stateless:** Logic App doesn't store workflow execution history (faster, cheaper)
- **Stateful:** Logic App stores history (allows retry, easier debugging)

Consumption tier uses **stateless by default**, which is fine for our audit pipeline.

---

## Common Questions

### Q: Can I edit the workflow later?

**A:** Yes! You can return to the Logic App Designer anytime by:
1. Going to the Azure Portal
2. Searching for your Logic App
3. Clicking **Logic app designer** in the left menu

All your changes are auto-saved.

### Q: What happens if I delete this Logic App?

**A:** It's gone. You'd need to recreate it from scratch in Lab 5. But don't worry — the configuration is simple and you can redo it quickly if needed.

### Q: Can I use Standard tier instead of Consumption?

**A:** Technically yes, but not recommended for this lab:
- Standard costs a fixed amount per hour (even if idle)
- Designed for production workloads with high throughput
- Overkill for learning — Consumption is more cost-effective

Stick with **Consumption** for this lab and reevaluate in production.

### Q: How do I test my workflow without uploading images?

**A:** You can manually trigger it:
1. In the Logic App overview, click **Run trigger** (manual button)
2. Choose a trigger to test
3. Provide sample data
4. Observe the execution

We'll do this in Lab 10 after building the complete workflow.

### Q: What if my workflow fails to execute?

**A:** Check the **Runs** tab in your Logic App:
1. In the left menu, click **Runs**
2. Each row is an execution attempt
3. Click a failed run to see the error
4. Error messages usually indicate which step failed and why
5. Return to the Designer, fix the step, and retry

---

## Preview: Labs 6-9 Workflow

Your completed workflow will look like this (we'll build it step by step):

```
Lab 6: Add Blob Storage Trigger
├─ Detect new images in audit-input
└─ Automatically start workflow

Lab 7: Add Document Intelligence HTTP Action
├─ Extract text and structure from image
└─ Output: JSON with layout, text, tables

Lab 8: Add Data Operations & OpenAI HTTP Action
├─ Parse Document Intelligence response
├─ Format prompt for OpenAI
├─ Call OpenAI API for audit analysis
└─ Output: Approval/rejection + confidence + explanation

Lab 9: Add Output & Error Handling
├─ Compose final JSON result
├─ Write result to audit-output container
└─ Add error handling if anything fails
```

Each lab adds one or more steps. By Lab 9, you'll have a complete, automated audit pipeline.

---

## Security & Post-Lab Hardening

This lab creates a basic Logic App for learning. For production use, implement these hardening steps **after** you complete the core labs (Labs 0-11):

1. **Use Managed Identity** — Authenticate Logic App with system-assigned identity instead of connection strings (more secure)
2. **Enable request authentication** — Require API keys or OAuth for HTTP triggers (if applicable)
3. **Implement error alerts** — Set up Azure Monitor alerts for failed workflow runs
4. **Use Azure Key Vault** — Store sensitive secrets (API keys) in Key Vault instead of `.env` files
5. **Enable workflow logging** — Azure Diagnostics → Log Analytics for audit trails
6. **Implement rate limiting** — Prevent runaway executions if triggers fire unexpectedly

See [Logic App security best practices](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-securing-a-logic-app) for more.

---

## Next Steps

You've successfully created your Logic App! Before proceeding to Lab 6, review:

✅ **Lab 5 complete:**
- Logic App created (Consumption tier)
- Designer accessible
- Connectors searchable
- Workflow blank and ready

**Lab 6 (next):** Add the Blob Storage trigger ("When a blob is created")

---

[← Previous: Deploy Azure Blob Storage Account](lab-04-storage.md)

[Next: Add Image Upload Trigger →](lab-06-trigger.md)

---

*Lab 5 created by Bond. Last updated: March 2026.*
