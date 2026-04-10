# Email to Xero API Support

---

**To**: api@xero.com
**Subject**: OAuth Error: "unauthorized_client" on New Web App - Unable to Authorize

---

## Issue Summary

I'm experiencing a persistent OAuth 2.0 authorization error when attempting to connect my web application to Xero. The error occurs at Xero's authorization server level before any request reaches my application.

**Error Details:**
- Error: `unauthorized_client`
- Message: "Unknown client or client not enabled"
- Error Code: 500
- Occurs at: `https://login.xero.com/identity/connect/authorize`

---

## Application Details

**App Name**: CoKeeper
**App Type**: Web app
**Client ID**: `FA06820111BE4134A16F655183CF1772`
**Integration Purpose**: Transaction categorization assistant that learns from users' historical coding patterns

**OAuth Configuration:**
- Redirect URI: `https://unliteralised-dante-sniffly.ngrok-free.dev/api/xero/callback`
- Scopes Requested: `openid profile email offline_access accounting.transactions.read accounting.contacts.read accounting.settings.read`
- Authorization URL: Generated using standard OAuth 2.0 flow

---

## Xero Account Details

**Account Type**: Trial account with Demo Company (US)
**Demo Company**: Created and active
**Plan**: Starter plan (0 of 5 connections used)

---

## Troubleshooting Steps Already Taken

I have systematically verified all configuration:

### 1. App Configuration ✅
- Confirmed app type is "Web app" (OAuth 2.0)
- Redirect URI saved correctly in Configuration section
- Client Secret generated and stored securely
- Company URL configured

### 2. Credentials ✅
- Client ID and Client Secret match exactly between Xero app and application
- No typos or whitespace issues
- Credentials tested in isolation

### 3. Demo Company ✅
- Created Demo Company (US) specifically for API testing
- Demo company is active and accessible
- Attempted to authorize with demo company

### 4. Network/Technical ✅
- Using ngrok for HTTPS tunnel (Xero requires HTTPS)
- Redirect URI accessible and responding correctly
- Backend server running and receiving requests
- No proxy or firewall blocking

### 5. Verification ✅
- Checked Logs section: No authorization attempts logged (requests never reach app)
- Checked Connection management: 0 connections (as expected)
- Checked Manage Plan: Starter plan allows 5 connections
- Checked Collaborators: No organization restrictions

---

## Observed Behavior

When initiating OAuth flow:

1. Application redirects to Xero authorization URL with correct parameters
2. User sees Xero error page immediately (no login prompt)
3. Error message: "Sorry, something went wrong... Error: unauthorized_client... Unknown client or client not enabled"
4. **No requests appear in application Logs** (error occurs at Xero's server)

This suggests the issue is server-side at Xero, not in my application configuration.

---

## Request for Assistance

Could you please:

1. **Verify** if my Client ID (`FA06820111BE4134A16F655183CF1772`) is properly enabled for OAuth
2. **Check** if there are any server-side restrictions on my app preventing authorization
3. **Confirm** if trial accounts with demo companies can use OAuth (documentation suggests yes)
4. **Review** any account-level settings that might block OAuth flows

---

## Additional Context

- App created: April 9, 2026
- Time since creation: Same day (possible propagation delay?)
- Previous OAuth experience: Successfully implemented QuickBooks OAuth with similar architecture
- Testing environment: Local development with ngrok HTTPS tunnel

---

## Expected vs Actual Behavior

**Expected**:
- User redirects to Xero login page
- User selects Demo Company (US)
- User approves requested permissions
- Xero redirects back to my callback URL with authorization code

**Actual**:
- User sees error 500 immediately
- No login prompt
- No organization selection
- No approval screen
- Requests never logged in app

---

## Questions

1. Are there any additional steps required to "enable" a newly created web app for OAuth?
2. Do trial accounts have restrictions on OAuth that demo companies don't bypass?
3. Is there a propagation delay for new app configurations?
4. Are there any server-side logs you can check for my Client ID?

---

## Contact Information

I'm available for any follow-up questions or additional troubleshooting steps you might suggest.

Thank you for your assistance in resolving this issue.

Best regards,
[Your Name]

---

**Attachments** (if possible):
- Screenshot of app Configuration page showing redirect URI
- Screenshot of error message from Xero authorization page
- Screenshot of Logs section showing no entries
