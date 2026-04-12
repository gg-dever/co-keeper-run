# CoKeeper Demo Strategy

How to demo CoKeeper to others **before** QuickBooks production approval.

---

## 🎯 The Challenge

**Problem:** QuickBooks sandbox mode only works with developer accounts
**Solution:** Focus on CSV workflow and Xero OAuth for demos

---

## ✅ What Works for Demos TODAY

### **1. CSV Workflow (BEST for demos)**

**Why:**
- No accounts needed
- Works immediately
- Shows core AI functionality
- Zero barriers to entry

**How to demo:**

1. **Provide sample CSV files** (see below)
2. User uploads training CSV
3. User uploads new transactions CSV
4. See predictions with confidence tiers
5. Export results

**Who can use it:** ANYONE

---

### **2. Xero OAuth (Works with real accounts)**

**Why:**
- Xero has no sandbox mode
- Already works with real Xero accounts
- Production-ready today

**How to demo:**

1. User clicks "Connect Xero"
2. Logs in with real Xero account
3. Fetches real transactions
4. Trains model
5. Gets predictions

**Who can use it:** Anyone with Xero account (~3.5M businesses worldwide)

---

### **3. QuickBooks OAuth (NOT ready for public demos)**

**Current Status:** Sandbox only

**Who can use it:**
- ✅ You (the developer)
- ✅ Other developers with QB sandbox accounts
- ❌ General public
- ❌ Real QuickBooks users

**When it works for everyone:** After production approval (needs domain)

---

## 📊 Sample CSV Files for Demos

Create these sample files for users to try:

### **QuickBooks Training CSV** (`qb_training_sample.csv`)

```csv
Date,Vendor,Amount,Memo,Current Category
2024-01-05,Amazon Web Services,150.00,Monthly hosting,Web Hosting & Services
2024-01-10,Office Depot,45.99,Paper and supplies,Office Supplies
2024-01-15,Starbucks,12.50,Client meeting,Meals & Entertainment
2024-01-20,Adobe Creative Cloud,54.99,Design software,Software & Subscriptions
2024-01-25,FedEx,28.75,Package delivery,Shipping & Delivery
2024-02-01,Amazon Web Services,150.00,Monthly hosting,Web Hosting & Services
2024-02-08,Uber,35.40,Trip to airport,Travel - Local
2024-02-12,LinkedIn Premium,29.99,Professional networking,Software & Subscriptions
2024-02-18,Dropbox Business,15.00,Cloud storage,Software & Subscriptions
2024-02-22,Office Depot,67.80,Printer ink,Office Supplies
2024-03-01,Amazon Web Services,150.00,Monthly hosting,Web Hosting & Services
2024-03-05,Zoom Video Communications,14.99,Video conferencing,Software & Subscriptions
2024-03-10,Starbucks,18.75,Team coffee,Meals & Entertainment
2024-03-15,United Airlines,450.00,Flight to conference,Travel - Airfare
2024-03-20,Hilton Hotels,289.00,Conference hotel,Travel - Lodging
```

### **QuickBooks Prediction CSV** (`qb_predict_sample.csv`)

```csv
Date,Vendor,Amount,Memo
2024-04-01,Amazon Web Services,150.00,Monthly hosting
2024-04-05,Starbucks,15.30,Morning coffee
2024-04-08,Microsoft 365,12.99,Office subscription
2024-04-12,FedEx,42.50,Client documents
2024-04-15,Office Depot,89.25,New printer
```

### **Xero Training CSV** (`xero_training_sample.csv`)

```csv
Date,Contact,Description,Amount,Related account
2024-01-05,AWS,Monthly hosting,150.00,Web Hosting
2024-01-10,Office Depot,Office supplies,45.99,Office Expenses
2024-01-15,Starbucks,Client meeting,12.50,Entertainment
2024-01-20,Adobe,Creative Cloud,54.99,Software
2024-01-25,FedEx,Package delivery,28.75,Postage
2024-02-01,AWS,Monthly hosting,150.00,Web Hosting
2024-02-08,Uber,Airport transport,35.40,Travel
2024-02-12,LinkedIn,Premium account,29.99,Software
2024-02-18,Dropbox,Cloud storage,15.00,Software
2024-02-22,Office Depot,Printer ink,67.80,Office Expenses
```

### **Xero Prediction CSV** (`xero_predict_sample.csv`)

```csv
Date,Contact,Description,Amount
2024-04-01,AWS,Monthly hosting,150.00
2024-04-05,Starbucks,Coffee break,15.30
2024-04-08,Microsoft,Office 365,12.99
2024-04-12,FedEx,Document shipping,42.50
2024-04-15,Office Depot,New equipment,89.25
```

---

## 🎬 Demo Script

### **For Live Demos**

**Opening (30 seconds):**
"CoKeeper uses AI to automatically categorize your accounting transactions. Let me show you how it works with a real example."

**CSV Demo (2 minutes):**

1. "First, we upload historical transactions that are already categorized"
   - Upload `qb_training_sample.csv`
   - Shows 15 transactions, AI training progress

2. "The AI learns your categorization patterns in seconds"
   - Model trains (5-10 seconds)
   - Shows training summary

3. "Now we upload new uncategorized transactions"
   - Upload `qb_predict_sample.csv`
   - Shows 5 new transactions

4. "Watch the AI predict categories with confidence scores"
   - Green = High confidence (auto-approve)
   - Yellow = Medium (quick review)
   - Red = Low (needs attention)

5. "Export and import to QuickBooks/Xero"
   - Download CSV with predictions
   - Save hours of manual work

**Closing (30 seconds):**
"For QuickBooks and Xero users, you can connect directly via OAuth to fetch transactions automatically. Want to try it with your own data?"

---

## 🌐 Demo Landing Page

Create a simple demo page on your Streamlit app:

### **Homepage Message:**

```markdown
# Try CoKeeper Now

## Three Ways to Demo:

### 📁 CSV Upload (Try Immediately)
- Download sample files
- See AI predictions in seconds
- No account needed

[Download QuickBooks Sample] [Download Xero Sample]

### 🔗 Connect Xero (Real Accounts)
- Works with your real Xero account
- Fetch transactions automatically
- Production-ready today

[Connect Xero]

### 📊 QuickBooks OAuth
- Coming soon (pending production approval)
- Use CSV upload to try QuickBooks workflow
```

---

## 📈 Conversion Funnel

**Current (Pre-Production):**
1. Visitor arrives → Sees demo options
2. Downloads sample CSV OR connects Xero
3. Tries CSV workflow → Sees predictions
4. Impressed → Waits for QB production
5. Bookmarks for later

**After Production Approval:**
1. Visitor arrives → Sees all options
2. Connects QuickBooks OR Xero OR uploads CSV
3. Gets real predictions on real data
4. Becomes regular user
5. Tells colleagues

---

## 🎯 Marketing Message

**Current positioning:**

"Try CoKeeper's AI transaction categorization:
- ✅ CSV Upload: Try now with sample data
- ✅ Xero: Connect your account today
- 🔜 QuickBooks: Coming soon (pre-approval)"

**After production:**

"Try CoKeeper's AI transaction categorization:
- ✅ CSV Upload: Works with any accounting system
- ✅ Xero: Connect in 30 seconds
- ✅ QuickBooks: Connect in 30 seconds"

---

## 🚀 Timeline

### **TODAY**
- Share demo with CSV workflow
- Xero users can connect real accounts
- Use sample CSVs to show functionality

### **WEEK 1-2** (After domain + deployment)
- Get production QB credentials
- Submit app for approval
- Keep demoing CSV + Xero

### **WEEK 2-3** (After QB approval)
- QuickBooks production live
- All three workflows available
- Full public demo ready

---

## 💡 Pro Tips

1. **Lead with CSV demo**
   - Most accessible
   - Shows core AI functionality
   - Works for everyone

2. **Highlight Xero advantage**
   - "Already works with real accounts!"
   - Differentiator during pre-production

3. **Set QuickBooks expectations**
   - "QuickBooks OAuth coming soon"
   - "Try CSV version now to see how it works"

4. **Collect emails**
   - "Notify me when QuickBooks OAuth is ready"
   - Build launch list

5. **Create video demo**
   - Screen recording of CSV workflow
   - Share on LinkedIn, YouTube
   - Show predictions in action

---

## ✅ Action Items

**Create demo assets:**
- [ ] Sample CSV files (QB train/predict, Xero train/predict)
- [ ] Demo video (2-3 minutes)
- [ ] Screenshots for social media
- [ ] "Try Demo" button on homepage

**Update app messaging:**
- [ ] Add "Download Sample CSV" buttons
- [ ] Explain which workflows are available now
- [ ] Set expectations for QB OAuth timeline

**Track demo engagement:**
- [ ] How many CSV uploads?
- [ ] How many Xero connections?
- [ ] How many QB waitlist signups?

---

**Bottom Line:** Your CSV workflow is your best demo tool right now. It shows the core AI functionality without requiring any accounts. Perfect for portfolio demonstrations, LinkedIn posts, and general public demos!
