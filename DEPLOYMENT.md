# CoKeeper Deployment Guide

**Complete guide for deploying CoKeeper to production**

Choose your deployment method below based on your needs and technical comfort level.

---

## 🎯 Deployment Options

| Method | Cost | Difficulty | Best For |
|--------|------|------------|----------|
| **Render.com** | FREE or $14/mo | ⭐ Easy | Quick demos, no server management |
| **DigitalOcean** | $6/mo | ⭐⭐ Medium | Production, cost-effective |
| **Cloud Run** | $5-20/mo | ⭐⭐⭐ Advanced | Auto-scaling, enterprise |

---

## 🚀 Method 1: Render.com (Recommended for Quick Start)

**Pros**: GitHub auto-deploy, free tier, zero server management
**Cons**: Free tier sleeps after 15min inactivity (30s cold start)

### **Prerequisites**
- GitHub account
- QuickBooks/Xero OAuth apps configured

### **Steps**

#### **1. Push Code to GitHub**

```bash
cd /path/to/co-keeper-run
git init
git add .
git commit -m "Initial commit - Ready for deployment"

# Create repo at github.com/new, then:
git remote add origin https://github.com/YOUR-USERNAME/co-keeper-run.git
git branch -M main
git push -u origin main
```

#### **2. Connect to Render**

1. Go to: https://render.com
2. Sign up with GitHub account
3. **New → Blueprint**
4. Connect repository: `co-keeper-run`
5. Branch: `main`
6. Blueprint path: `render.yaml` (auto-detected)
7. Click **Apply**

Render will create:
- `cokeeper-backend` service
- `cokeeper-frontend` service

#### **3. Configure Environment Variables**

**Backend Service** (Go to service → Environment tab):

```bash
# QuickBooks OAuth
QB_CLIENT_ID=your_qb_client_id
QB_CLIENT_SECRET=your_qb_client_secret
QB_REDIRECT_URI=https://cokeeper-backend-xxxx.onrender.com/api/quickbooks/callback
QB_ENVIRONMENT=production

# Xero OAuth
XERO_CLIENT_ID=your_xero_client_id
XERO_CLIENT_SECRET=your_xero_client_secret
XERO_REDIRECT_URI=https://cokeeper-backend-xxxx.onrender.com/api/xero/callback

# Frontend URL
FRONTEND_URL=https://cokeeper-frontend-xxxx.onrender.com
```

**Frontend Service**:

```bash
BACKEND_URL=https://cokeeper-backend-xxxx.onrender.com
```

⚠️ **Replace `xxxx`** with your actual Render subdomain!

#### **4. Update OAuth Redirect URIs**

**QuickBooks**:
1. https://developer.intuit.com/app/developer/dashboard
2. Keys & OAuth → Redirect URIs
3. Add: `https://cokeeper-backend-xxxx.onrender.com/api/quickbooks/callback`

**Xero**:
1. https://developer.xero.com/app/manage/
2. OAuth 2.0 redirect URIs
3. Add: `https://cokeeper-backend-xxxx.onrender.com/api/xero/callback`

#### **5. Test Deployment**

Visit: `https://cokeeper-frontend-xxxx.onrender.com`

**First load may take 30 seconds (free tier cold start)**

### **Render Pricing**

- **Free**: $0/month (sleeps after 15min, 30s wake time)
- **Starter**: $7/service/month = $14/month total (always on, no sleep)

Upgrade anytime in Render dashboard: Service → Settings → Plan

### **Auto-Deploy on Git Push**

Every `git push` to main branch auto-deploys! 🎉

```bash
git add .
git commit -m "Update feature"
git push
# Render automatically rebuilds
```

---

## 💻 Method 2: DigitalOcean (Best Value for Production)

**Pros**: Full control, always-on, $6/month
**Cons**: Manual server setup, Docker required

### **Prerequisites**
- DigitalOcean account (or any VPS provider)
- Domain name
- SSH access to server

### **Steps**

#### **1. Create Droplet**

1. Go to: https://digitalocean.com
2. Create → Droplets
3. **Image**: Ubuntu 22.04 LTS
4. **Plan**: Basic ($6/month - 1GB RAM)
5. **Datacenter**: Choose closest to users
6. **SSH Keys**: Add your public key
7. Create Droplet → Note IP address

#### **2. Point Domain to Server**

In your domain registrar (Namecheap, Cloudflare, etc.):

```
Type: A
Host: cokeeper (or @)
Value: your.droplet.ip.address
TTL: 3600
```

Wait 10-30 minutes for DNS propagation.

#### **3. SSH Into Server**

```bash
ssh root@your.droplet.ip.address
```

#### **4. Install Docker**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

#### **5. Clone Repository**

```bash
git clone https://github.com/yourusername/co-keeper-run.git
cd co-keeper-run
```

#### **6. Get SSL Certificate**

```bash
# Install certbot
sudo apt install certbot -y

# Get certificate for your domain
sudo certbot certonly --standalone -d cokeeper.yourdomain.com

# Certificates saved to:
# /etc/letsencrypt/live/cokeeper.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/cokeeper.yourdomain.com/privkey.pem

# Copy to project
mkdir -p ssl
sudo cp /etc/letsencrypt/live/cokeeper.yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/cokeeper.yourdomain.com/privkey.pem ssl/
sudo chmod 644 ssl/*.pem
```

#### **7. Configure Environment**

```bash
# Copy template
cp .env.production .env

# Edit with your values
nano .env
```

**Update these values**:

```env
# Your domain
DOMAIN=cokeeper.yourdomain.com
FRONTEND_URL=https://cokeeper.yourdomain.com
BACKEND_URL=https://cokeeper.yourdomain.com/api

# QuickBooks Production
QB_CLIENT_ID=your_qb_client_id
QB_CLIENT_SECRET=your_qb_client_secret
QB_REDIRECT_URI=https://cokeeper.yourdomain.com/api/quickbooks/callback
QB_ENVIRONMENT=production

# Xero Production
XERO_CLIENT_ID=your_xero_client_id
XERO_CLIENT_SECRET=your_xero_client_secret
XERO_REDIRECT_URI=https://cokeeper.yourdomain.com/api/xero/callback
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

#### **8. Deploy**

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy!
./deploy.sh
```

Or manually:

```bash
docker-compose build
docker-compose up -d
```

#### **9. Verify Deployment**

```bash
# Check containers are running
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoint
curl https://cokeeper.yourdomain.com/api/health
```

Visit: `https://cokeeper.yourdomain.com`

### **DigitalOcean Management Commands**

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild and restart
docker-compose build
docker-compose up -d

# Update from Git
git pull
docker-compose build
docker-compose up -d
```

### **SSL Auto-Renewal**

```bash
# Test renewal
sudo certbot renew --dry-run

# Set up auto-renewal (cron)
sudo crontab -e

# Add this line:
0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/cokeeper.yourdomain.com/*.pem /path/to/co-keeper-run/ssl/ && docker-compose restart nginx
```

---

## ☁️ Method 3: Google Cloud Run

**Pros**: Auto-scaling, pay-per-use, enterprise-grade
**Cons**: More complex setup, can be expensive at scale

### **Prerequisites**
- Google Cloud account
- `gcloud` CLI installed
- Docker installed locally

### **Steps**

#### **1. Build and Push Containers**

```bash
# Set project
gcloud config set project your-project-id

# Build backend
cd backend
docker build -t gcr.io/your-project-id/cokeeper-backend .
docker push gcr.io/your-project-id/cokeeper-backend

# Build frontend
cd ../frontend
docker build -t gcr.io/your-project-id/cokeeper-frontend .
docker push gcr.io/your-project-id/cokeeper-frontend
```

#### **2. Deploy to Cloud Run**

```bash
# Deploy backend
gcloud run deploy cokeeper-backend \
  --image gcr.io/your-project-id/cokeeper-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars QB_CLIENT_ID=xxx,QB_CLIENT_SECRET=xxx,...

# Deploy frontend
gcloud run deploy cokeeper-frontend \
  --image gcr.io/your-project-id/cokeeper-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BACKEND_URL=https://cokeeper-backend-xxx.run.app
```

#### **3. Configure Domain (Optional)**

```bash
# Map custom domain
gcloud run services update cokeeper-frontend \
  --region us-central1 \
  --add-custom-domain cokeeper.yourdomain.com
```

---

## 🔐 OAuth App Configuration

### **QuickBooks Production**

1. **Create Production App**:
   - Go to: https://developer.intuit.com/app/developer/dashboard
   - Create new app or switch existing to production

2. **Configure App** Settings:
   - **Redirect URI**: `https://your-domain.com/api/quickbooks/callback`
   - **Scopes**: `com.intuit.quickbooks.accounting`
   - **Host domain**: `your-domain.com`
   - **Launch URL**: `https://your-domain.com/`
   - **Terms of Service**: `https://your-domain.com/terms`
   - **Privacy Policy**: `https://your-domain.com/privacy`

3. **Submit for Review** (for production OAuth):
   - App description
   - Support email
   - Wait 3-5 business days for approval

4. **Copy Credentials**:
   - Client ID
   - Client Secret

### **Xero Production**

1. **Create App**:
   - Go to: https://developer.xero.com/app/manage/
   - Create new app

2. **Configure App**:
   - **Redirect URI**: `https://your-domain.com/api/xero/callback`
   - **Scopes**: Check all accounting scopes

3. **Copy Credentials**:
   - Client ID
   - Client Secret

**⚠️ Note**: Xero apps work with real accounts immediately (no approval needed)

---

## ✅ Post-Deployment Checklist

### **Test CSV Workflow**
- [ ] Upload training CSV
- [ ] Model trains successfully
- [ ] Upload prediction CSV
- [ ] Get predictions with confidence tiers
- [ ] Export results

### **Test OAuth Workflows**

**Xero** (works immediately):
- [ ] Click "Connect Xero"
- [ ] Authenticate with real Xero account
- [ ] Fetch transactions
- [ ] Train model
- [ ] Get predictions

**QuickBooks** (after production approval):
- [ ] Click "Connect QuickBooks"
- [ ] Authenticate with real QB account
- [ ] Fetch transactions
- [ ] Train model
- [ ] Get predictions

### **Verify Pages**
- [ ] Frontend loads: `https://your-domain.com`
- [ ] Backend health: `https://your-domain.com/api/health`
- [ ] Terms page: `https://your-domain.com/terms`
- [ ] Privacy page: `https://your-domain.com/privacy`

### **Check Security**
- [ ] All URLs use HTTPS
- [ ] OAuth secrets not exposed in client-side code
- [ ] CORS configured correctly

---

## 🐛 Troubleshooting

### **"OAuth callback failed"**
- Check redirect URI exactly matches in OAuth app settings
- Ensure HTTPS (not HTTP)
- Verify no trailing slashes

### **"Backend unhealthy"**
- Check environment variables are set
- View logs: `docker-compose logs backend` or Render dashboard
- Verify OAuth credentials are correct

### **"Cannot connect to backend"**
- Check `BACKEND_URL` in frontend environment
- Test backend health: `curl https://backend-url/api/health`
- Check firewall/security groups allow traffic

### **"Free tier sleep is too slow"**
- Upgrade to Render Starter plan ($7/service)
- Or switch to DigitalOcean ($6/month total)

### **"SSL certificate expired"**
- Renew: `sudo certbot renew`
- Restart nginx: `docker-compose restart nginx`

---

## 💰 Cost Comparison

| Platform | Monthly Cost | Setup Time | Always-On? |
|----------|-------------|------------|------------|
| **Render Free** | $0 | 30 min | ❌ (sleeps) |
| **Render Starter** | $14 | 30 min | ✅ |
| **DigitalOcean** | $6 | 1-2 hours | ✅ |
| **Cloud Run** | $5-20 | 1 hour | ✅ |

---

## 📊 Monitoring

### **Render**
- Dashboard → Logs tab
- Auto-monitoring included

### **DigitalOcean**

```bash
# View real-time logs
docker-compose logs -f

# Check resource usage
docker stats

# Monitor disk space
df -h
```

### **Health Check Endpoint**

Visit: `https://your-domain.com/api/health`

Returns:
```json
{
  "status": "healthy",
  "qb_model_loaded": true,
  "xero_model_loaded": false,
  "qb_oauth_available": true,
  "xero_oauth_available": true
}
```

---

## 🔄 Continuous Deployment

### **Render** (Auto)
Every `git push` auto-deploys! Just commit and push.

### **DigitalOcean** (Manual)

```bash
ssh root@your-server
cd co-keeper-run
git pull
docker-compose build
docker-compose up -d
```

Or set up GitHub Actions (advanced).

---

## 🎯 Next Steps After Deployment

1. **Test end-to-end** with real data
2. **Get QuickBooks production credentials** (if sandbox)
3. **Submit QB app for review** (3-5 days)
4. **Share frontend URL** with test users
5. **Monitor logs** for errors
6. **Collect feedback** and iterate

---

## 🆘 Need Help?

- **Render Issues**: https://render.com/docs
- **Docker Issues**: https://docs.docker.com/
- **OAuth Setup**: See [OAUTH_PRODUCTION_SETUP.md](OAUTH_PRODUCTION_SETUP.md)
- **Legal Pages**: See [LEGAL_PAGES_SETUP.md](LEGAL_PAGES_SETUP.md)

---

**You're ready to deploy!** Choose your method above and follow the steps. 🚀
