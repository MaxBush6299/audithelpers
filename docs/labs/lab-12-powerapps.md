# Lab 12: Power Apps Audit Portal (Optional)

**Estimated duration:** 60 minutes  
**Owner:** Q  
**Objective:** Build a Power Apps canvas application to view audit results, manually approve/reject verdicts, and interact with the pipeline without the Azure Portal.

> **🎯 Optional Lab:** This lab is bonus content for extending the audit pipeline with a user-friendly frontend. Complete Lab 11 before starting.

---

## What You'll Learn

In this lab, you will:

- ✅ Create a canvas Power App from scratch in the Power Apps maker portal
- ✅ Add and configure the Azure Blob Storage connector
- ✅ Build an upload screen with file picker to upload evidence images
- ✅ Build a results gallery screen that displays JSON verdicts from `audit-output`
- ✅ Build a detail view to inspect individual audit results
- ✅ Add approve/reject buttons with local override capability
- ✅ Understand how non-technical auditors interact with the pipeline
- ✅ Navigate between screens using Power Apps navigation

---

## Prerequisites

Before starting this lab, ensure you have:

- ✅ **Lab 11 complete** — Your Logic App is running and producing JSON results in `audit-output` blob container
- ✅ **Power Apps access** — You have a Power Apps maker environment (included with Microsoft 365 or standalone Power Apps license)
- ✅ **Storage Account credentials** — From Lab 4: Storage account name and access key stored in your `.env` file
- ✅ **Initials ready** — For app naming convention

---

## Why Power Apps for Audit Portals?

**Power Apps** is a low-code/no-code platform for building business applications. For this audit pipeline, it enables:

| Capability | Benefit | Use in This Lab |
|---|---|---|
| **Canvas apps** | Build custom UI without web development | Design audit dashboard |
| **Data connectors** | Pre-built integrations to Azure services | Connect to Blob Storage |
| **No-code logic** | Use formulas instead of code | Upload files, filter results, approve/reject |
| **Responsive design** | Works on desktop, tablet, mobile | Auditors can review on any device |
| **Portal-native** | Build entirely in maker.powerapps.com | No local development environment needed |

**Why NOT Dataverse for this lab:**
- Dataverse adds complexity (additional licensing, data synchronization)
- For this proof-of-concept, we'll use local app state and manual override
- Extension labs can add Dataverse persistence and Power Automate notifications

---

## What You'll Build

Your completed Power App will have **three screens:**

```
┌──────────────────────────────────────────────┐
│     UPLOAD SCREEN (Home)                     │
├──────────────────────────────────────────────┤
│                                              │
│  [File Picker]                               │
│  Select image from computer                  │
│                                              │
│  [Upload Button]                             │
│  Upload to audit-input container             │
│                                              │
│  [Status: Ready to upload]                   │
│                                              │
│  [→ View Results]  [← Refresh]               │
│                                              │
└──────────────────────────────────────────────┘
              ↓ [View Results]
┌──────────────────────────────────────────────┐
│     RESULTS GALLERY (Browse)                 │
├──────────────────────────────────────────────┤
│                                              │
│  [⟳ Refresh Results]                         │
│                                              │
│  Result 1: File.jpg | ✓ APPROVED            │
│  Result 2: File2.jpg | ✗ REJECTED           │
│  Result 3: File3.jpg | ? PENDING             │
│                                              │
│  [→ View Details]                            │
│                                              │
│  [← Back to Upload]                          │
│                                              │
└──────────────────────────────────────────────┘
              ↓ [View Details]
┌──────────────────────────────────────────────┐
│     DETAIL VIEW (Inspect)                    │
├──────────────────────────────────────────────┤
│                                              │
│  Image Name: File.jpg                        │
│  Status: APPROVED                            │
│  Confidence: 95%                             │
│                                              │
│  Verdict:                                    │
│  [Full JSON verdict displayed]               │
│                                              │
│  Manual Override:                            │
│  [Approve] [Reject] [Clear Override]         │
│                                              │
│  [← Back to Results]                         │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Step 1: Open Power Apps Maker Portal

### 1.1 Navigate to Power Apps

1. Go to [make.powerapps.com](https://make.powerapps.com)
2. Sign in with your Microsoft 365 or Power Apps account
3. You should see the **Power Apps Home** page with options to create apps

### 1.2 Understand the Maker Portal

The Power Apps maker portal has these main sections:

- **Home** — Recent apps, templates, learning resources
- **Apps** — List of your existing apps
- **Create** — Templates and blank apps
- **Data** — Connectors and data sources
- **Build** — The design canvas (opens when you create/edit an app)

---

## Step 2: Create a Blank Canvas App

### 2.1 Start App Creation

1. On the Power Apps Home page, click **Create** (left menu)
2. Under **Start from blank**, click **Canvas app**
   - If prompted for app name, enter: `AuditPortal-{your-initials}` (e.g., `AuditPortal-Q`)
3. When prompted for format, select **Tablet layout** (landscape)
   - Tablet layout gives you more horizontal space for galleries

### 2.2 Wait for the Designer to Load

Power Apps will load the designer. This takes ~30 seconds. You should see:

- **Left sidebar:** Navigation pane (screens, components, connectors)
- **Center canvas:** Your blank app (white rectangle)
- **Right panel:** Properties and controls
- **Top toolbar:** Save, Publish, Share buttons

> **💡 Tip:** If the designer doesn't load, refresh the page or try a different browser (Edge or Chrome recommended).

---

## Step 3: Configure the Azure Blob Storage Connector

### 3.1 Add the Connector

1. In the left sidebar, click **Data** (folder icon)
2. Click **+ Add data**
3. Search for **Azure Blob Storage**
4. Click on **Azure Blob Storage** (the official Microsoft connector)
5. You'll be prompted to sign in — use your Azure credentials

### 3.2 Configure Connection Details

After signing in, you'll see a form to connect to your storage account:

1. **Storage account name:** Enter the name from Lab 4 (e.g., `storageauditjs`)
   - Check your `.env` file if unsure
2. **Storage account access key:** Paste the primary access key from Lab 4
   - In Azure Portal: Storage Account → Access keys → Key 1 → Copy the key value
3. Click **Create** or **Connect**

> **⚠️ Important:** Keep the access key secure. Never commit it to version control. In production, use a Managed Identity or Stored Connection instead.

The connector is now available in your app. You'll see **Azure Blob Storage** listed under **Data** in the left sidebar.

---

## Step 4: Rename and Create Screens

### 4.1 Rename the Default Screen

Power Apps creates a default screen called **Screen1**. Let's rename it:

1. In the left sidebar, right-click **Screen1**
2. Select **Rename**
3. Type: `UploadScreen`
4. Press Enter

### 4.2 Create the Results Screen

1. In the left sidebar, click **+ New screen**
2. Select **Blank** layout
3. Rename it to `ResultsScreen` (right-click → Rename)

### 4.3 Create the Detail Screen

1. In the left sidebar, click **+ New screen**
2. Select **Blank** layout
3. Rename it to `DetailScreen` (right-click → Rename)

You should now have three screens:
- UploadScreen
- ResultsScreen
- DetailScreen

---

## Step 5: Build the Upload Screen

The Upload Screen allows auditors to select and upload image files to the `audit-input` container.

### 5.1 Add Title

1. Make sure **UploadScreen** is selected (highlighted in left sidebar)
2. In the toolbar, click **Insert** (or the **+** icon)
3. Select **Text label**
4. A label appears on the canvas. In the top-right Properties panel:
   - Set **Text** to: `"Upload Evidence Image"`
   - Set **Font size** to: `28`
   - Set **Alignment** to: `Center`
5. Drag the label to the top-center of the canvas

### 5.2 Add File Upload Control (Attachment)

1. Click **Insert**
2. Search for or select **Attachment**
   - This is Power Apps' file picker control
3. Place it in the center of the screen
4. In Properties (right panel):
   - Set **Name** to: `FilePickerControl`
   - This will store the selected file

> **💡 Note:** The Attachment control allows users to select one or more files. For this lab, we'll accept single files.

### 5.3 Add Upload Button

1. Click **Insert**
2. Select **Button**
3. Place it below the file picker
4. In Properties:
   - Set **Text** to: `"Upload to Audit Input"`
   - Set **Name** to: `UploadButton`
5. Now set the button's **OnSelect** action:
   - In the formula bar (top), click in the **OnSelect** field
   - Paste this formula (replace with your container and storage config):
     ```
     Set(UploadStatus, "Uploading...");
     'Azure Blob Storage'.CreateFile(
       "audit-input",
       FilePickerControl.Value.FileName,
       FilePickerControl.Value
     );
     Set(UploadStatus, "Upload successful!");
     ClearCollect(FileList, FilePickerControl.Value);
     Clear(FilePickerControl)
     ```
   - This formula:
     - Sets a status message
     - Uploads the file to the `audit-input` container
     - Clears the file picker for next upload

> **⚠️ Important:** Replace container name and storage account details with your actual values from Lab 4.

### 5.4 Add Status Label

1. Click **Insert** → **Text label**
2. Place it below the upload button
3. In Properties:
   - Set **Text** to: `UploadStatus` (this variable was created in the OnSelect formula)
   - Set **Font size** to: `14`
   - Set **Color** to: `Blue`
4. This will display upload status messages to the user

### 5.5 Add Navigation Buttons

1. Click **Insert** → **Button**
2. Place it at the bottom of the screen
3. Set **Text** to: `"View Results →"`
4. Set **OnSelect** to:
   ```
   Navigate(ResultsScreen, ScreenTransition.Fade)
   ```
5. Create another button next to it:
   - **Text:** `"⟳ Refresh"`
   - **OnSelect:** `Refresh('Azure Blob Storage')`

Your Upload Screen is now complete!

---

## Step 6: Build the Results Gallery Screen

The Results Screen displays all JSON files from the `audit-output` container in a scrollable list.

### 6.1 Add Title

1. Make sure **ResultsScreen** is selected
2. Click **Insert** → **Text label**
3. Set **Text** to: `"Audit Results"`
4. Set **Font size** to: `28`
5. Place at the top-center

### 6.2 Add Refresh Button

1. Click **Insert** → **Button**
2. Set **Text** to: `"⟳ Refresh Results"`
3. Set **OnSelect** to:
   ```
   ClearCollect(
     ResultsList,
     'Azure Blob Storage'.ListFiles("audit-output").value
   )
   ```
4. Click the button once to load initial results
   - This creates a collection called `ResultsList` with all files from `audit-output`

### 6.3 Add Gallery Control

1. Click **Insert** → **Gallery**
2. Select **Vertical** layout
3. Resize the gallery to fill most of the screen (below the title and refresh button)
4. In Properties:
   - Set **Items** to: `ResultsList`
   - Set **Name** to: `ResultsGallery`

### 6.4 Customize Gallery Items

Power Apps creates a default gallery template. You need to customize what's displayed:

1. Click on the gallery area
2. Look for the **gallery template** (it should show "Title", "Subtitle", "Body" fields)
3. Delete the default fields and add custom ones:
   - Click the first field (usually "Title") → Delete
   - Repeat for other fields
4. Now add new fields:
   - Click **Insert** → **Text label** (place it in the gallery template)
   - Set the label's **Text** to: `ThisItem.Name`
   - This displays the file name

5. Add another label below it for status:
   - Click **Insert** → **Text label**
   - Set **Text** to:
     ```
     If(
       Find("APPROVED", Upper(ThisItem.Name)) > 0,
       "✓ APPROVED",
       If(
         Find("REJECTED", Upper(ThisItem.Name)) > 0,
         "✗ REJECTED",
         "? PENDING"
       )
     )
     ```
   - This reads the file name to infer status (you can enhance this later to parse JSON)

6. Add a button to view details:
   - Click **Insert** → **Button**
   - Set **Text** to: `"→ Details"`
   - Set **OnSelect** to:
     ```
     Set(SelectedResult, ThisItem);
     Navigate(DetailScreen, ScreenTransition.Fade)
     ```

### 6.5 Add Back Button

1. At the bottom of the screen, click **Insert** → **Button**
2. Set **Text** to: `"← Back to Upload"`
3. Set **OnSelect** to:
   ```
   Navigate(UploadScreen, ScreenTransition.Fade)
   ```

Your Results Screen is now complete!

---

## Step 7: Build the Detail Screen

The Detail Screen shows the full JSON verdict for a selected result and allows manual approve/reject override.

### 7.1 Add Header

1. Make sure **DetailScreen** is selected
2. Click **Insert** → **Text label**
3. Set **Text** to: `"Audit Result Details"`
4. Set **Font size** to: `28`
5. Place at the top-center

### 7.2 Display Selected File Name

1. Click **Insert** → **Text label**
2. Set **Text** to: `"File: " & SelectedResult.Name`
3. Set **Font size** to: `16`
4. Place below the header

### 7.3 Display the Full JSON

1. Click **Insert** → **Text input** (to display multi-line JSON)
2. In Properties:
   - Set **Default** to: `SelectedResult.DisplayName`
   - Or set **Text** to display the full file content
3. Set **Multiline** to: `On`
4. Set **Mode** to: `Read-only` (to prevent editing)
5. Resize to fill most of the screen

> **💡 Note:** To display the actual JSON content, you'd need to read the blob file content using:
> ```
> 'Azure Blob Storage'.GetFileContentAsText("audit-output", SelectedResult.Name)
> ```
> This requires additional configuration in Step 7.4.

### 7.4 Add a Rich Text Display (Better for JSON)

If the text input doesn't display well:

1. Delete the text input from 7.3
2. Click **Insert** → **HTML text**
3. Set **HTML Text** to:
   ```
   "<pre>" & 'Azure Blob Storage'.GetFileContentAsText(
     "audit-output",
     SelectedResult.Name
   ) & "</pre>"
   ```
4. This fetches and displays the actual JSON file content in a formatted way

> **⚠️ Important:** The `GetFileContentAsText` action reads the blob file. This might require the blob to contain JSON text. If blobs are binary or encrypted, adjust as needed.

### 7.5 Add Approve/Reject/Override Buttons

1. Below the JSON display, click **Insert** → **Button**
2. Create three buttons:

   **Button 1: Approve**
   - **Text:** `"✓ Approve"`
   - **OnSelect:**
     ```
     Set(ManualOverride, "APPROVED");
     Set(OverrideStatus, "Manual override set to APPROVED")
     ```

   **Button 2: Reject**
   - **Text:** `"✗ Reject"`
   - **OnSelect:**
     ```
     Set(ManualOverride, "REJECTED");
     Set(OverrideStatus, "Manual override set to REJECTED")
     ```

   **Button 3: Clear Override**
   - **Text:** `"Clear Override"`
   - **OnSelect:**
     ```
     Set(ManualOverride, "");
     Set(OverrideStatus, "Override cleared")
     ```

3. Add a label to show override status:
   - Click **Insert** → **Text label**
   - Set **Text** to: `OverrideStatus`
   - Set **Color** to: `Green` (to indicate successful override)

### 7.6 Add Back Button

1. Click **Insert** → **Button**
2. Set **Text** to: `"← Back to Results"`
3. Set **OnSelect** to:
   ```
   Navigate(ResultsScreen, ScreenTransition.Fade)
   ```

Your Detail Screen is now complete!

---

## Step 8: Test Navigation and Save

### 8.1 Test the App

1. In the top toolbar, click the **▶ Play** button (or press **F5**)
2. Test the following flows:
   - ✅ **Upload Screen:** Appears with title, file picker, upload button
   - ✅ **Navigation:** Click "View Results →" — should navigate to Results Screen
   - ✅ **Results Screen:** Shows "Audit Results" and refresh button
   - ✅ **Navigation back:** Click "← Back to Upload" — returns to Upload Screen
   - ✅ **Gallery:** Click "⟳ Refresh Results" to load files (may be empty if no audit-output files yet)
   - ✅ **Detail View:** Click "→ Details" on a gallery item — navigates to Detail Screen
   - ✅ **Approve/Reject:** Click approve/reject buttons — status message updates

3. When satisfied, press **Escape** to exit preview mode

### 8.2 Save the App

1. In the top toolbar, click **Save**
2. Enter a description (optional):
   - `"Audit Portal for reviewing pipeline results and manual overrides"`
3. Click **Save** again

---

## Step 9: Publish the App

### 9.1 Publish to Power Apps

1. Click the **Publish** button in the top toolbar
2. A dialog appears — click **Publish this version**
3. Wait for the publish to complete (~30 seconds)

Your app is now published and available in:
- Power Apps Home → Apps (listed)
- Power Apps Mobile (if installed on your phone)
- Power Apps web portal

### 9.2 Share with Team

To let others use your app:

1. Click **Share** (top toolbar)
2. Enter team members' email addresses
3. Select **Can use** (or **Can edit** if they'll make changes)
4. Click **Share**

---

## Step 10: Extend and Enhance (Optional Improvements)

Your Power App is now functional. Here are enhancements for future work:

### 10.1 Parse JSON Properly

Currently, the app reads file names to infer status. For production:

1. Use the **JSON** function to parse the JSON content:
   ```
   Set(
     ParsedResult,
     JSON(
       'Azure Blob Storage'.GetFileContentAsText(
         "audit-output",
         SelectedResult.Name
       )
     )
   );
   Set(Status, ParsedResult.verdict);
   Set(Confidence, ParsedResult.confidence)
   ```

2. Update labels to display parsed fields:
   - Status: `ParsedResult.verdict`
   - Confidence: `ParsedResult.confidence & "%"`
   - Explanation: `ParsedResult.explanation`

### 10.2 Add Dataverse Integration

For persistent storage of approvals:

1. In Power Apps, click **Data** → **+ Add data**
2. Create a new Dataverse table called `AuditOverrides`
3. Add columns: `FileName`, `OriginalVerdict`, `OverrideStatus`, `Notes`, `OverrideDate`
4. In the Detail Screen, add a Power Automate cloud flow to write overrides to Dataverse when approve/reject is clicked

### 10.3 Add Power Automate Notifications

Notify team members when an override is applied:

1. Go to [make.powerautomate.com](https://make.powerautomate.com)
2. Create a cloud flow triggered by Dataverse record creation (AuditOverrides table)
3. Add an action: **Send an email** (Office 365 Outlook)
4. Configure email to alert auditors of overrides

### 10.4 Add Audit Point Maintenance Screen

Create a screen to view and update audit points (criteria):

1. Add a new screen called `AuditPointsScreen`
2. Add a gallery showing current audit points from a JSON configuration blob
3. Add edit/delete controls to modify audit points
4. Write changes back to blob storage

### 10.5 Add Image Preview

Display uploaded images in the Detail Screen:

1. In the Detail Screen, add an **Image** control
2. Set its **Image** source to:
   ```
   'Azure Blob Storage'.GetFileContent("audit-input", SelectedResult.Name)
   ```
3. This will display the uploaded evidence image for visual review

---

## Architecture Diagram: App Flow

```
User (Auditor)
      ↓
[Power Apps Canvas App]
      ↓
    ┌─────────────────┬──────────────────┬──────────────────┐
    │                 │                  │                  │
[Upload Screen]  [Results Screen]   [Detail Screen]
    │                 │                  │
    ├→ File Picker    ├→ Gallery         ├→ JSON Display
    ├→ Upload Button  ├→ Refresh         ├→ Approve/Reject
    └→ Status Label   └→ Navigation      └→ Manual Override
           ↓                ↓                    ↓
    [Azure Blob Storage]    ↓              [Local State]
    ├─ audit-input          ├─ audit-output   (SelectedResult,
    └─ (receives files)     └─ (reads files)   ManualOverride)
           ↓
    [Logic App Pipeline]
    (Labs 6-10)
```

---

## Key Concepts

### Power Apps Connectors

**Connectors** are bridges between Power Apps and external services (like Azure Blob Storage). They provide:

- **Actions:** What the service can do (upload file, read file, list files)
- **Authentication:** Secure connection using credentials or Managed Identity
- **Data types:** Automatic conversion between app and service formats

In this lab, we used the **Azure Blob Storage connector** to:
- List files from containers
- Upload files to containers
- Read file content as text

### Variables and Collections

- **Variables** store single values: `Set(UploadStatus, "Success")`
- **Collections** store lists of records: `ClearCollect(ResultsList, ...)`
- Both reset when the app closes; for persistence, use Dataverse or databases

### Navigation Patterns

```
Navigate(ScreenName, ScreenTransition.Fade)
```

- **ScreenName:** Target screen (must match screen name exactly)
- **ScreenTransition:** Animation effect (Fade, Pop, Push, None)

---

## Common Questions

### Q: Can I upload images directly from a mobile phone?

**A:** Yes! Power Apps works on phones and tablets. The file picker adapts to mobile:
- On phones: Opens device file browser (Photos, Documents, etc.)
- On tablets/desktop: Opens file explorer
- Install Power Apps Mobile from your phone's app store

### Q: What if I want to approve/reject and persist the change?

**A:** The current app stores overrides in app memory, which clears when the app closes. To persist:

1. Add a Dataverse table (see 10.2)
2. Modify the Approve/Reject buttons to write to Dataverse:
   ```
   Patch(AuditOverrides, {
     FileName: SelectedResult.Name,
     OverrideStatus: "APPROVED",
     OverrideDate: Now()
   })
   ```

### Q: How do I parse the JSON verdict from audit-output files?

**A:** Use the **JSON** function (or **ParseJSON** in some Power Apps versions):

```
Set(
  VerDict,
  JSON(FileContent).verdict
);
```

This assumes the blob file contains valid JSON. If you're unsure of the JSON structure, download a sample from the Azure Portal and inspect it.

### Q: Can I edit the Logic App trigger directly from Power Apps?

**A:** Not in this lab design. The Logic App triggers on blob uploads; Power Apps just uploads files. To edit Logic App logic:
- Go to Azure Portal → Logic App → Designer
- Modify the workflow (triggers, actions, conditions)

Power Apps complements the Logic App; they don't directly control each other.

### Q: What if the file upload fails?

**A:** The app will show an error in the status label. Common causes:

- **Wrong storage account name:** Check `.env` file and verify spelling
- **Invalid access key:** Regenerate key in Azure Portal → Storage Account → Access keys
- **Insufficient permissions:** Ensure your Azure account has Contributor access to the storage account
- **Container doesn't exist:** Verify `audit-input` container exists (created in Lab 4)

Go to Azure Portal to verify storage account status, then retry.

---

## Security Considerations

This lab uses **basic authentication** (storage account access key). For production, implement:

1. **Managed Identity** — Use Power Apps Managed Identity instead of storing keys
2. **Row-level security (RLS)** — Control which auditors see which results
3. **Audit logging** — Log all approve/reject actions for compliance
4. **Encryption** — Ensure blobs are encrypted at rest and in transit
5. **Access controls** — Limit Power Apps access to specific users/groups

---

## Post-Lab Checklist

Before considering this lab complete:

- ✅ Power App created and named `AuditPortal-{initials}`
- ✅ Three screens functional: Upload, Results, Detail
- ✅ Azure Blob Storage connector configured
- ✅ File upload working (test with a small image)
- ✅ Navigation between screens working
- ✅ Approve/Reject buttons functional
- ✅ App saved and published
- ✅ Shared with team members (optional)

---

## What Your Completed Audit Portal Does

Your Power App now provides:

1. **Non-Portal Access** — Auditors don't need Azure Portal access to view results
2. **User-Friendly Interface** — Click-and-review instead of navigating Azure blobs
3. **Manual Override** — Auditors can approve/reject verdicts and record decisions
4. **Audit Trail** — All approvals are visible in the app (with Dataverse integration, persisted)
5. **Extensibility** — Easy to add notifications, data storage, reporting

This completes the audit pipeline front-end. The next step (if desired) is connecting Power Automate for notifications and Dataverse for persistence.

---

## Extensions and Future Work

### Short-term Enhancements
- Add image preview in Detail Screen
- Parse JSON verdicts and display structured results
- Add search/filter gallery by file name or status
- Add date range filter for results

### Medium-term Enhancements
- Integrate Dataverse for approval audit trail
- Add Power Automate notifications (email, Teams)
- Create audit point maintenance screen
- Add reporting views (approvals per auditor, trends)

### Long-term Enhancements
- Build model-driven app for complex workflows
- Integrate with Power BI for audit analytics
- Add AI Builder models for automated image classification
- Connect to customer's existing ERP/audit systems

---

## Next Steps

Congratulations! You've completed the optional Power Apps lab. Your audit pipeline is now end-to-end:

✅ **Lab 0-10:** Logic App pipeline running  
✅ **Lab 11:** End-to-end testing verified  
✅ **Lab 12:** Power Apps portal for auditors (optional, complete!)

---

[← Previous: End-to-End Testing](lab-11-testing.md)  
[🏁 Return to Lab Series Home](../index.md)

---

*Lab 12 created by Q. Last updated: March 2026.*
