# QuickBooks App Setup - Legal Pages URLs

When setting up your QuickBooks OAuth app for production, you'll need to provide these URLs:

---

## 📋 Required URLs for QuickBooks App

### **1. Terms of Service / EULA**
**Field:** "End-User License Agreement"
**URL:** `https://your-domain.com/terms`

**Example:** `https://cokeeper.yourdomain.com/terms`

### **2. Privacy Policy**
**Field:** "Privacy Policy"
**URL:** `https://your-domain.com/privacy`

**Example:** `https://cokeeper.yourdomain.com/privacy`

---

## ✅ What I've Created

I've created professional legal documents for you:

1. **Terms of Service** (`frontend/static/terms.html`)
   - Covers service description, user responsibilities
   - AI prediction disclaimers
   - Liability limitations
   - Data usage and privacy

2. **Privacy Policy** (`frontend/static/privacy.html`)
   - What data we collect
   - How we use it
   - Data security measures
   - User rights (GDPR compliant)

---

## 🔧 How to Customize

### **Before Deploying, Update These:**

**In `terms.html` (line 137):**
```html
<strong>Email:</strong> support@yourdomain.com<br>
<strong>Website:</strong> https://yourdomain.com
```

**In `privacy.html` (line 259):**
```html
<strong>Email:</strong> privacy@yourdomain.com<br>
<strong>Website:</strong> https://yourdomain.com
```

**In both files:**
- Replace `[Your State/Country]` with your jurisdiction (line 125 in terms.html)
- Update contact email addresses
- Add your company name if applicable

---

## 🌐 How They Work

The URLs are served by nginx from the `frontend/static/` directory:

- `https://your-domain.com/terms` → `frontend/static/terms.html`
- `https://your-domain.com/privacy` → `frontend/static/privacy.html`

After deployment, these pages will be publicly accessible at those URLs.

---

## 📝 Using in QuickBooks Developer Portal

1. **Go to:** https://developer.intuit.com/app/developer/dashboard
2. **Select your app**
3. **Go to "App Settings"**
4. **Fill in legal URLs:**
   - **End-User License Agreement:** `https://your-domain.com/terms`
   - **Privacy Policy:** `https://your-domain.com/privacy`
5. **Save changes**

✅ **Include the `https://` protocol** (required by QuickBooks)

---

## 🧪 Testing the URLs

After deployment, verify they work:

```bash
# Test Terms of Service
curl https://your-domain.com/terms

# Test Privacy Policy
curl https://your-domain.com/privacy

# Or open in browser:
# https://your-domain.com/terms
# https://your-domain.com/privacy
```

---

## ⚠️ Important Notes

1. **Must be HTTPS** - QuickBooks requires secure URLs
2. **Must be publicly accessible** - Anyone can view these pages
3. **Cannot be login-protected** - No authentication required
4. **Must be your domain** - Cannot use third-party hosting

---

## 📖 Legal Disclaimer

The provided templates are starting points based on standard SaaS terms. Consider:

- Having a lawyer review for your specific jurisdiction
- Adding company-specific clauses
- Ensuring compliance with local laws (GDPR, CCPA, etc.)
- Updating as your service evolves

---

**You're ready to submit your QuickBooks app for review!** 🎉

Use these URLs in your app settings:
- **EULA:** `https://your-domain.com/terms`
- **Privacy:** `https://your-domain.com/privacy`
