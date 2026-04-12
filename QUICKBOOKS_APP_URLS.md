# QuickBooks App Configuration - URLs

When setting up your QuickBooks OAuth app in the Intuit Developer Portal, you'll need to provide several URLs. Here's what to enter:

---

## 🌐 Required URLs

### **1. Host Domain** ⭐
**What it is:** Your application's base domain (without `https://` or paths)

**Format:** `yourdomain.com`

**Examples:**
- Production: `cokeeper.com`
- Subdomain: `app.yourdomain.com`
- Development: `localhost` (for local testing)

**⚠️ Important:**
- **NO** `https://`
- **NO** `www.`
- **NO** paths like `/api`
- Just the domain name

---

### **2. Launch URL**
**What it is:** Where users land after successfully connecting QuickBooks

**Format:** `https://yourdomain.com/quickbooks-connected`

**What to enter:** `https://yourdomain.com/`

**Why:** After OAuth completes, redirect users to your home page where they can start using the app.

**Recommended:** `https://yourdomain.com/`

---

### **3. Disconnect URL**
**What it is:** Where QuickBooks sends users when they disconnect your app

**Format:** `https://yourdomain.com/disconnect`

**What to enter:** `https://yourdomain.com/`

**Why:** When users revoke access in QuickBooks settings, send them back to your home page.

**Recommended:** `https://yourdomain.com/`

---

### **4. Connect/Reconnect URL**
**What it is:** Where users go to start the OAuth connection flow

**Format:** `https://yourdomain.com/connect`

**What to enter:** `https://yourdomain.com/`

**Why:** This is where users click to begin connecting their QuickBooks account.

**Recommended:** `https://yourdomain.com/`

---

## 📋 Quick Reference

Copy these values for your QuickBooks app settings:

```
Host domain:              yourdomain.com
Launch URL:               https://yourdomain.com/
Disconnect URL:           https://yourdomain.com/
Connect/reconnect URL:    https://yourdomain.com/
```

**Replace `yourdomain.com` with your actual domain!**

---

## 🔄 How Our OAuth Flow Works

Our current implementation handles OAuth internally:

1. **User clicks "Connect QuickBooks"** (in Streamlit at `/`)
2. **Backend generates OAuth URL** (`/api/quickbooks/connect`)
3. **User authorizes in QuickBooks** (Intuit's site)
4. **QuickBooks redirects to callback** (`/api/quickbooks/callback`)
5. **Backend exchanges code for tokens** (automatic)
6. **User returns to Streamlit** (home page)

**All these URLs point to your home page** because the OAuth flow is handled by API endpoints, not separate pages.

---

## 🔐 OAuth Redirect URI (Different from above!)

**This is SEPARATE from the URLs above.**

In the "Keys & OAuth" section, you'll also configure:

**Redirect URIs:** (for OAuth callback)
- Production: `https://yourdomain.com/api/quickbooks/callback`
- Local dev: `https://your-ngrok-url.ngrok-free.app/api/quickbooks/callback`

**Why different?**
- **Redirect URI** = Technical OAuth callback endpoint (backend)
- **Launch/Connect URLs** = User-facing pages (frontend)

---

## 📝 Complete Configuration Example

### **Production Deployment**

```
=== App Settings ===
Host domain:              cokeeper.com
Launch URL:               https://cokeeper.com/
Disconnect URL:           https://cokeeper.com/
Connect/reconnect URL:    https://cokeeper.com/

=== Keys & OAuth ===
Redirect URIs:            https://cokeeper.com/api/quickbooks/callback

=== Legal Pages ===
Terms of Service:         https://cokeeper.com/terms
Privacy Policy:           https://cokeeper.com/privacy
```

### **Local Development (with ngrok)**

```
=== App Settings ===
Host domain:              localhost
Launch URL:               http://localhost:8501/
Disconnect URL:           http://localhost:8501/
Connect/reconnect URL:    http://localhost:8501/

=== Keys & OAuth ===
Redirect URIs:            https://unliteralised-dante-sniffly.ngrok-free.dev/api/quickbooks/callback

=== Legal Pages ===
(Use production URLs or temporary hosting)
```

---

## ✅ Validation Checklist

Before submitting:

- [ ] Host domain has NO `https://` (just `yourdomain.com`)
- [ ] Launch URL points to your home page
- [ ] All URLs use `https://` (not `http://`) for production
- [ ] Redirect URI (in Keys & OAuth) points to `/api/quickbooks/callback`
- [ ] Legal page URLs are publicly accessible
- [ ] Test OAuth flow works with all URLs

---

## 🧪 Testing the URLs

After configuration, test the full flow:

1. **Visit Connect URL** → Should show your app's home page
2. **Click "Connect QuickBooks"** → Starts OAuth flow
3. **Authorize in QuickBooks** → QuickBooks login page
4. **After authorization** → Redirects to callback, then launch URL
5. **Should land on** → Your home page with "Connected" status

---

## 🔧 Current Backend Configuration

Your `.env` file should have:

```bash
# QuickBooks OAuth
QB_CLIENT_ID=your_production_client_id
QB_CLIENT_SECRET=your_production_client_secret
QB_REDIRECT_URI=https://yourdomain.com/api/quickbooks/callback
QB_ENVIRONMENT=production
```

Make sure `QB_REDIRECT_URI` matches the redirect URI in QuickBooks settings!

---

## 📖 Common Issues

### **"Redirect URI mismatch"**
- Ensure `QB_REDIRECT_URI` in `.env` exactly matches redirect URI in QuickBooks app
- Check for trailing slashes (use none: `.../callback` not `.../callback/`)

### **"Invalid host domain"**
- Remove `https://` from host domain
- Remove `www.` prefix
- Use just the domain: `yourdomain.com`

### **"Launch URL not accessible"**
- Ensure your domain is live and accessible
- Test with `curl https://yourdomain.com/`
- Check SSL certificate is valid

### **"Users land on wrong page after OAuth"**
- The launch URL is just a reference - QuickBooks doesn't actually redirect there
- Our callback endpoint handles the redirect back to Streamlit
- Users should land on your home page automatically

---

## 🎯 Summary

**Simple answer:**
- **Host domain:** `yourdomain.com` (no https)
- **All other URLs:** `https://yourdomain.com/` (your home page)

**Why it's simple:**
CoKeeper handles OAuth flow internally through API endpoints. All these URLs point to your home page because users start and end their journey there.

**The only technical URL that matters:**
- **Redirect URI** (in Keys & OAuth): `https://yourdomain.com/api/quickbooks/callback`

---

**You're ready to configure your QuickBooks app!** 🚀
