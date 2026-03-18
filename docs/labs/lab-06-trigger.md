---
layout: default
title: Lab 6: Blob Trigger
parent: Labs
nav_order: 7
---
# Lab 6: Add Image Upload Trigger

**Time required:** 15 minutes  
**Learning objectives:**
- Configure a Blob Storage trigger in a Logic App
- Understand trigger parameters (container, polling interval)
- Test the trigger with a sample image upload

---

## What is a Trigger?

A **trigger** is an event that starts your Logic App workflow. Think of it as the "watch for this event" instruction. In this lab, your trigger will be:

> "When a blob (file) is added or modified in the `audit-input` storage container, start the workflow."

### Polling vs. Push Triggers

Azure Blob Storage uses a **polling-based trigger**, meaning:
- Logic App checks the storage container on a schedule (e.g., every 1 minute)
- When it detects a new or modified blob, it starts a run
- This is reliable for our use case and doesn't require additional infrastructure

**Trigger output:** When a blob is detected, the trigger provides data such as:
- Blob name (filename)
- Blob path
- Blob properties (size, created/modified dates)

This data flows into your workflow actions for processing.

---

## Prerequisites

- **Lab 5 completed:** You have a Logic App deployed and open in the Designer
- **Storage Account created:** The Storage Account from Lab 0 with the `audit-input` container
- **Connection string available:** From your `.env` file (format: `DefaultEndpointProtocol=https;...`)

---

## Step 1: Open Your Logic App in the Designer

1. Go to [portal.azure.com](https://portal.azure.com)
2. In the search bar, type **Logic Apps** and select it
3. Find and click your Logic App from Lab 5 (e.g., `audit-logic-app`)
4. In the left menu, click **Logic App Designer**
   - You should see the blank workflow canvas or your existing workflow

---

## Step 2: Add the Blob Storage Trigger

1. In the Designer canvas, click **+** (or click the existing trigger if one is present to replace it)
2. In the **Choose an operation** search box, type **blob** to filter connectors
3. Look for the **Azure Blob Storage** connector (from Microsoft)
4. Under that connector, select the trigger named **When a blob is added or modified (properties only)**

   > **Why "properties only"?** This version triggers on blob properties changes (like file upload), which is efficient for polling. The alternative "When a blob is created" (for file systems) is not suitable here.

---

## Step 3: Create the Storage Account Connection

When you select the trigger, a panel appears asking for a connection.

1. In the **Connection Name** field, enter a descriptive name (e.g., `AuditStorageConnection`)
2. Click **Change connection**
3. Select **Use connection string** (or create a new connection)
4. Paste your Storage Account connection string from your `.env` file
   - Format: `DefaultEndpointProtocol=https;AccountName=XXXXX;AccountKey=XXXXX;EndpointSuffix=core.windows.net`
5. Click **Create** or **Sign in** to validate the connection

---

## Step 4: Configure Trigger Parameters

Once the connection is established, you'll see a configuration panel with these fields:

### Container
1. Click the **Container** dropdown
2. Select **audit-input** (the container you created in Lab 0)
3. If it doesn't appear, verify:
   - The container exists in your Storage Account
   - The connection string is correct

### Number of Blobs to Return
1. In the **Number of blobs to return** field, enter **1**
   - This keeps each run focused on one blob at a time
   - Production systems might use 10–50 depending on throughput

### How Often to Check (Polling Interval)
1. In the **How often to check for items** dropdown, select a frequency
   - **For testing:** Select **1 Minute** (fast feedback)
   - **For production:** Select **5 Minutes** or **1 Hour** (reduces API calls and cost)

2. In the **Interval** field, the value auto-fills (e.g., `1` for 1 minute)

### Final Configuration

Your trigger configuration should look like this:

| Parameter | Value |
|-----------|-------|
| Container | `audit-input` |
| Number of blobs to return | 1 |
| How often to check for items | 1 Minute |
| Interval | 1 |

---

## Step 5: Save the Logic App

1. At the top of the Designer, click **Save**
   - Wait for the confirmation message: "Logic app saved"
2. The trigger is now active and will begin polling the `audit-input` container

---

## Step 6: Test the Trigger

### Upload a Sample Image

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for and open your **Storage Account** (from Lab 0)
3. In the left menu, click **Containers**
4. Click the **audit-input** container
5. Click **Upload** at the top
6. Select or drag a sample image file (any `.jpg`, `.png`, or similar)
   - Example: A photo, screenshot, or test document
7. Click **Upload**

### Check Logic App Execution

1. Go back to your Logic App in the Azure portal
2. Click **Runs history** (or **Overview** → scroll to see recent runs)
3. You should see a new run that started shortly after the upload
   - Status: `Succeeded` or `Running`
4. Click the run to see details:
   - **Inputs:** The trigger detected the blob (blob name, path, properties)
   - **Outputs:** Shows the data passed to the next action (if any)

**Successful test:** If the run appears and the trigger fired, your trigger is working correctly.

---

## Troubleshooting

### Trigger Not Firing?

**Issue:** You uploaded an image but no run appeared.

**Solutions:**
1. **Check the connection:**
   - Go to Logic App Designer → Click the trigger
   - Verify the Storage Account connection string is valid
   - Try clicking **Test** in the trigger panel to validate connectivity

2. **Verify the container name:**
   - Confirm the container is named exactly `audit-input` (case-sensitive in some contexts)
   - Go to Storage Account → Containers and check the exact name

3. **Wait for the polling interval:**
   - If you set the interval to 5 minutes, wait up to 5 minutes
   - For immediate testing, set it to 1 minute temporarily

4. **Check trigger history:**
   - In Logic App Designer, expand the trigger and click **Trigger history**
   - This shows the last checks and any errors

### Permission Issues

**Issue:** Error: "Authorization failed" or "Access Denied" when creating the connection.

**Solutions:**
1. Verify the Storage Account connection string:
   - Go to Storage Account → Access keys
   - Copy the full connection string (not just the account name)
   - Make sure it includes `AccountKey=`

2. Ensure the Storage Account allows connections:
   - If you have a firewall rule, add your client IP (or Logic App managed identity, if configured)
   - For Lab purposes, you can use the default settings

3. Test the connection:
   - In Logic App Designer, delete the trigger and re-add it
   - Paste the connection string again carefully

---

## Key Concepts Summary

| Concept | What It Does |
|---------|--------------|
| **Trigger** | Detects the blob upload and starts the workflow |
| **Polling** | Logic App checks the container on a schedule (every 1 minute) |
| **Container** | The `audit-input` folder in Blob Storage where audit images go |
| **Polling Interval** | How often Logic App checks for new blobs (1 min for testing, 5+ min for production) |
| **Trigger Output** | Blob name, path, and properties used by downstream actions |

---

## Next Steps

- In Lab 7, you'll connect a **Document Intelligence** action to process the image
- The trigger's blob data will flow into Document Intelligence for text extraction
- This creates the foundation for your audit analysis workflow

---

## Navigation

[← Previous: Create the Logic App](lab-05-logic-app.md)

[Next: Integrate Document Intelligence →](lab-07-doc-intel.md)
