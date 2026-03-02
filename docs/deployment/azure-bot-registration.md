# Azure Bot Service Registration

> **These are manual steps in the Azure portal — no code required.**
> Complete these steps once before deploying A.T.L.A.S. to production.

---

## Prerequisites

- An Azure subscription (free tier works for dev/test)
- Your A.T.L.A.S. droplet deployed and domain pointed (e.g. `atlas.yourcompany.com`)
- SSL certificate in place (see `docs/deployment/droplet-deploy.md`)

---

## Step 1: Register the Bot in Azure Portal

1. Go to [portal.azure.com](https://portal.azure.com) and sign in
2. Click **Create a resource** → search for **"Azure Bot"** → click Create
3. Fill in the form:
   | Field | Value |
   |-------|-------|
   | Bot handle | `atlas-bot` |
   | Subscription | Your Azure subscription |
   | Resource group | Create new: `atlas-rg` |
   | Pricing tier | **F0** (free) for dev — **S1** for production |
   | App type | **Multi Tenant** |
   | Creation type | Create new Microsoft App ID |
4. Click **Review + Create** → **Create**
5. Wait for deployment to complete (~1–2 minutes)

---

## Step 2: Get App ID and Password

1. Open the newly created Bot resource
2. Go to **Configuration** in the left sidebar
3. Copy the **Microsoft App ID** → add to your `.env` as:
   ```
   MICROSOFT_APP_ID=<paste here>
   ```
4. Click **Manage** (next to the App ID) — this opens App Registrations
5. Go to **Certificates & secrets** → **New client secret**
   - Description: `atlas-prod`
   - Expires: 24 months (or per your security policy)
6. Click **Add** — **copy the secret Value immediately** (it won't be shown again)
7. Add to your `.env` as:
   ```
   MICROSOFT_APP_PASSWORD=<paste here>
   ```

---

## Step 3: Set the Messaging Endpoint

1. Return to your Bot resource → **Configuration**
2. Set **Messaging endpoint** to:
   ```
   https://atlas.yourcompany.com/api/messages
   ```
   *(Replace `atlas.yourcompany.com` with your actual domain)*
3. Click **Apply** / **Save**

---

## Step 4: Add Microsoft Teams Channel

1. In your Bot resource → **Channels** (left sidebar)
2. Click **Add a channel** → select **Microsoft Teams**
3. Accept the Microsoft Teams Channel Terms of Service
4. Click **Agree** → **Save**
5. The Teams channel should now show as **Running**

---

## Step 5: Test with Bot Framework Emulator (Local Dev)

Before deploying to production, test locally:

1. Download [Bot Framework Emulator](https://github.com/microsoft/BotFramework-Emulator/releases)
2. Start your local A.T.L.A.S. app: `uvicorn main:app --reload`
3. Open the Emulator → **Open Bot**
4. Set Bot URL: `http://localhost:8000/api/messages`
5. Leave App ID and App Password blank for local testing (emulator bypasses auth)
6. Click **Connect**
7. Send a test message: `how do I clear my browser cookies?`
8. Verify A.T.L.A.S. responds with the KB guide

---

## Step 6: Test in Microsoft Teams

1. In Azure portal → Bot resource → **Channels** → Teams → click **Open in Teams**
2. A Teams window opens with the bot
3. Send: `hello` — expect A.T.L.A.S. welcome message
4. Send: `my email isn't working` — expect triage questions

---

## Step 7: Publish App to Teams (Optional — for wider org rollout)

To deploy as an org-wide Teams app (vs. personal sideloading):

1. Go to [Teams Admin Center](https://admin.teams.microsoft.com)
2. **Teams apps** → **Manage apps** → **Upload new app**
3. Upload the Teams app manifest zip (generated from Bot Framework portal)
4. Assign to users/groups as needed

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `401 Unauthorized` on `/api/messages` | Wrong App ID/Password in `.env` | Re-check credentials from Azure portal |
| Bot not responding in Teams | Messaging endpoint not saved | Re-check Step 3, ensure HTTPS domain is reachable |
| `503` in emulator | App not running locally | Run `uvicorn main:app --reload` |
| Emulator works, Teams doesn't | Firewall/networking issue | Ensure port 443 open on droplet; check Nginx logs |
| `The app manifest is invalid` | Teams manifest format error | Re-download from Bot Framework portal |

---

## Environment Variables Checklist

After completing these steps, your `.env` should have:

```bash
MICROSOFT_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_APP_PASSWORD=your-client-secret-value
```

These are required for production Bot Framework authentication. Without them, all `/api/messages` requests will return 401.
