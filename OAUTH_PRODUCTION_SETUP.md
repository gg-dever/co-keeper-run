# OAuth Production Setup Guide

**How to enable real QuickBooks and Xero account connections (not sandbox)**

---

## 🎯 Current Status: Sandbox Mode

Your app is currently configured for **sandbox/development** mode, which means:
- ❌ Only works with QuickBooks sandbox test companies
- ❌ Users can't connect their real QuickBooks accounts
- ✅ Xero works with all accounts (no sandbox mode)

---

## 🔄 Switching to Production Mode

### **QuickBooks: Sandbox → Production**

QuickBooks has **two separate environments**:
- **Sandbox**: For testing only (what you have now)
- **Production**: For real customer accounts

#### **Step 1: Get Production Credentials**

1. **Go to QuickBooks Developer Portal**
   - Visit: https://developer.intuit.com/app/developer/dashboard
   - Log in with your Intuit account

2. **Find Your App**
   - Click on your app name
   - You should see "Keys & OAuth" tab

3. **Switch to Production**
   - You'll see two sections: **Sandbox Keys** and **Production Keys**
   - Copy your **Production Client ID** and **Production Client Secret**
   - ⚠️ **These are different from sandbox credentials!**

#### **Step 2: Update Environment Variable**

In your `backend/.env` file:

```env
# Change this line:
QB_ENVIRONMENT=sandbox

# To this:
QB_ENVIRONMENT=production

# And update credentials:
QB_CLIENT_ID=your_production_client_id_here
QB_CLIENT_SECRET=your_production_client_secret_here
```

#### **Step 3: Important - App Review Process**

⚠️ **QuickBooks Production Access Requires Approval**

Before your app can access real customer data in production:

1. **Complete App Profile**
   - Go to your app settings in the developer portal
   - Fill out all required information:
     - App name
     - App description
     - Privacy policy URL
     - Terms of service URL
     - Support contact

2. **Submit for Review**
   - QuickBooks reviews all production apps
   - Review typically takes 3-5 business days
   - They'll check:
     - ✅ Privacy policy exists
     - ✅ Terms of service exists
     - ✅ App description is clear
     - ✅ OAuth scopes are appropriate

3. **While Waiting for Approval**
   - You can still use your own QuickBooks account
   - Other users will see "This app is in development" message
   - After approval, any user can connect

#### **Step 4: Update Redirect URI**

Make sure your production redirect URI is set in the QuickBooks app settings:

- **Development**: `http://localhost:8000/api/quickbooks/callback`
- **Production**: `https://your-domain.com/api/quickbooks/callback`

You can have **both** redirect URIs registered at the same time!

---

### **Xero: Already Works with Real Accounts**

✅ **Good news**: Xero doesn't have separate sandbox/production modes!

Your current Xero setup **already works** with real accounts. However:

#### **Verify Xero App Status**

1. **Go to Xero Developer Portal**
   - Visit: https://developer.xero.com/app/manage/
   - Find your app

2. **Check App Status**
   - Should say "Published" or "Ready to Use"
   - If it says "Draft", click "Publish"

3. **Verify Scopes**
   - Make sure required scopes are enabled:
     - ✅ `openid`
     - ✅ `profile`
     - ✅ `email`
     - ✅ `offline_access`
     - ✅ `accounting.settings.read`
     - ✅ `accounting.transactions.read`
     - ✅ `accounting.contacts.read`

4. **Verify Redirect URI**
   - Should match: `https://your-domain.com/api/xero/callback`

**That's it!** Xero is ready for real accounts.

---

## 🚀 Quick Setup Comparison

### **For Local Development (localhost)**

```env
# QuickBooks - Sandbox
QB_ENVIRONMENT=sandbox
QB_CLIENT_ID=sandbox_client_id
QB_CLIENT_SECRET=sandbox_secret
QB_REDIRECT_URI=https://your-ngrok-url.ngrok-free.dev/api/quickbooks/callback

# Xero - Works with real accounts
XERO_CLIENT_ID=your_xero_client_id
XERO_CLIENT_SECRET=your_xero_secret
XERO_REDIRECT_URI=https://your-ngrok-url.ngrok-free.dev/api/xero/callback
```

### **For Production (your domain)**

```env
# QuickBooks - Production (after approval)
QB_ENVIRONMENT=production
QB_CLIENT_ID=production_client_id
QB_CLIENT_SECRET=production_secret
QB_REDIRECT_URI=https://your-domain.com/api/quickbooks/callback

# Xero - Same as before
XERO_CLIENT_ID=your_xero_client_id
XERO_CLIENT_SECRET=your_xero_secret
XERO_REDIRECT_URI=https://your-domain.com/api/xero/callback
```

---

## 📋 Checklist: Enable Real Account Connections

### **QuickBooks Production Checklist**

- [ ] Create production OAuth app in QuickBooks Developer Portal
- [ ] Get production Client ID and Client Secret
- [ ] Update `backend/.env` with production credentials
- [ ] Change `QB_ENVIRONMENT=production`
- [ ] Set production redirect URI in app settings
- [ ] Create privacy policy and terms of service
- [ ] Submit app for QuickBooks review
- [ ] Wait for approval (3-5 days)
- [ ] Test with your own QuickBooks account first
- [ ] Deploy to production domain with HTTPS

### **Xero Production Checklist**

- [ ] Verify Xero app is "Published" (not Draft)
- [ ] Confirm all required scopes are enabled
- [ ] Set production redirect URI in app settings
- [ ] Update `backend/.env` with redirect URI
- [ ] Deploy to production domain with HTTPS
- [ ] Test connection with a real Xero account

---

## 🧪 Testing Production Mode

### **Test with Your Own Accounts First**

1. **Deploy to production domain** (with HTTPS)
2. **Connect YOUR QuickBooks account**
   - Click "Connect to QuickBooks"
   - Log in with your real QuickBooks credentials
   - You should see your real company data
3. **Connect YOUR Xero account**
   - Click "Connect to Xero"
   - Log in with your real Xero credentials
   - You should see your real organization data

### **Test with a Test User**

Before going fully public:
1. Ask a friend to test with their QB/Xero account
2. They should be able to:
   - Connect their account
   - See their real transaction data
   - Train a model
   - Get predictions

---

## ⚠️ Important Notes

### **QuickBooks Limitations**

- **Sandbox**: Unlimited for development
- **Production**: Limited free tier, then paid
  - Free: 100 requests/month per account
  - Paid: Varies by plan

### **Xero Limitations**

- **Rate Limits**: 60 requests/minute per user
- **Token Expiry**: 30 minutes (must refresh)
- **Organizations**: Users must select organization after OAuth

### **Privacy & Security**

When using production credentials:
- ✅ **DO** have a privacy policy
- ✅ **DO** have terms of service
- ✅ **DO** explain what data you access
- ✅ **DO** use HTTPS everywhere
- ❌ **DON'T** store raw credentials
- ❌ **DON'T** share user data with third parties
- ❌ **DON'T** modify transactions without explicit user approval

---

## 🔧 Configuration Files to Update

### **1. backend/.env**

```env
# QuickBooks Production
QB_ENVIRONMENT=production  # ← Change this!
QB_CLIENT_ID=ABC123...     # ← Production ID
QB_CLIENT_SECRET=xyz789... # ← Production Secret
QB_REDIRECT_URI=https://your-domain.com/api/quickbooks/callback

# Xero (same as before, already works with real accounts)
XERO_CLIENT_ID=FA06820...
XERO_CLIENT_SECRET=tguOpQ...
XERO_REDIRECT_URI=https://your-domain.com/api/xero/callback
```

### **2. QuickBooks App Settings (in Developer Portal)**

Add both redirect URIs:
- `http://localhost:8000/api/quickbooks/callback` (for local testing)
- `https://your-domain.com/api/quickbooks/callback` (for production)

### **3. Xero App Settings (in Developer Portal)**

Add both redirect URIs:
- `https://your-ngrok-url.ngrok-free.dev/api/xero/callback` (for local testing)
- `https://your-domain.com/api/xero/callback` (for production)

---

## 🎉 Success Criteria

Your OAuth is working with real accounts when:

✅ **QuickBooks**:
- User clicks "Connect to QuickBooks"
- Logs in with their real QuickBooks credentials
- Selects their real company
- Returns to your app with connection successful
- You can fetch their real transactions

✅ **Xero**:
- User clicks "Connect to Xero"
- Logs in with their real Xero credentials
- Selects their organization
- Returns to your app with connection successful
- You can fetch their real transactions

---

## 🆘 Troubleshooting

### **"This app is in development mode"**

**QuickBooks**: Your app hasn't been approved for production yet.
- **Fix**: Complete app profile and submit for review
- **Workaround**: Use your own QB account (app owner can always access)

### **"Invalid redirect URI"**

**Both platforms**: Redirect URI in code doesn't match app settings.
- **Fix**: Copy the exact redirect URI from your `.env` file
- Paste it into the OAuth app settings (QB or Xero developer portal)
- Make sure it includes `https://` and matches exactly

### **"Unauthorized - 401"**

**Both platforms**: Using sandbox credentials in production mode (or vice versa).
- **Fix**: Double-check you're using the right credentials
- QuickBooks: Verify `QB_ENVIRONMENT` matches your credentials
- Xero: Verify client ID/secret are correct

### **Connection works but no data shows**

**Both platforms**: OAuth succeeded but API calls failing.
- **Check**: Token refresh logic is working
- **Check**: Correct scopes are requested
- **Check**: API endpoint URLs are correct

---

## 📞 Getting Help

**QuickBooks Support**:
- Developer Portal: https://developer.intuit.com/app/developer/dashboard
- Forum: https://help.developer.intuit.com/s/
- Documentation: https://developer.intuit.com/app/developer/qbo/docs/

**Xero Support**:
- Developer Portal: https://developer.xero.com/app/manage/
- Support: https://developer.xero.com/support/
- Documentation: https://developer.xero.com/documentation/

---

## ✅ Ready to Go Live?

1. ✅ QuickBooks production credentials obtained
2. ✅ QuickBooks app submitted for review
3. ✅ Xero app published
4. ✅ `.env` updated with production settings
5. ✅ Privacy policy and terms of service created
6. ✅ App deployed to production domain with HTTPS
7. ✅ Tested with your own accounts successfully
8. ✅ Tested with a test user successfully

**You're ready to let real users connect their accounts!** 🚀
