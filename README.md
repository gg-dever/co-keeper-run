# CoKeeper

AI-powered transaction categorization for QuickBooks and Xero accounting platforms.

## 🎯 What is CoKeeper?

CoKeeper uses machine learning to automatically categorize financial transactions in QuickBooks and Xero. Train custom models on your historical data and get instant predictions for new transactions with confidence scores.

**Key Features:**
- ✅ QuickBooks & Xero integration via OAuth 2.0
- ✅ CSV upload workflow (no OAuth required)
- ✅ Custom ML models trained on YOUR data
- ✅ Confidence tiers (GREEN/YELLOW/RED) for predictions
- ✅ Interactive web UI with analytics dashboards
- ✅ Export predictions to CSV or Excel

---

## 🚀 Quick Start

### **Deploy to Production** (Show your work publicly)

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete guide with 3 deployment options:
- **Render.com** (FREE or $14/month, easiest, GitHub auto-deploy)
- **DigitalOcean** ($6/month, best value)
- **Google Cloud Run** ($5-20/month, auto-scaling)

**Quick Start - Render.com**:
```bash
# 1. Push to GitHub
git push

# 2. Connect to Render.com
# 3. Auto-deploys! Get public URL in 30 minutes
```

### **Run Locally** (Development/Testing)

See **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** for local development setup.

**Quick Start**:
```bash
# Backend
cd backend
uvicorn main:app --port 8002

# Frontend (new terminal)
cd frontend
streamlit run app.py

# Visit: http://localhost:8501
```

---

## 📚 Documentation

**Start Here**:
- 🏠 **[DOCS_GUIDE.md](DOCS_GUIDE.md)** - Documentation index (find everything)
- 🚀 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- 🎯 **[DEMO_STRATEGY.md](DEMO_STRATEGY.md)** - How to demo CoKeeper
- 🔐 **[OAUTH_PRODUCTION_SETUP.md](OAUTH_PRODUCTION_SETUP.md)** - Enable real QB/Xero accounts

**For AI Agents**:
- 🤖 **[CLAUDE.md](CLAUDE.md)** - Workspace orientation for AI assistants

---

## 💻 Local Development

### Prerequisites
- Python 3.12+
- Docker and Docker Compose

### Quick Start

```bash
# Start both services
docker-compose up

# Access the application
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Build Docker Images

```bash
# Make build script executable
chmod +x build-docker.sh

# Build both images
./build-docker.sh
```

## Google Cloud Run Deployment

### Prerequisites

1. **Google Cloud SDK**: Install from https://cloud.google.com/sdk/docs/install
2. **GCP Project**: Have a GCP project with billing enabled
3. **Set Environment Variables**:
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   export GCP_REGION="us-central1"  # Optional, defaults to us-central1
   ```

### Deploy to Cloud Run

```bash
# Make deploy script executable
chmod +x deploy-cloud-run.sh

# Deploy both services
./deploy-cloud-run.sh
```

The script will:
1. Enable required GCP APIs (Cloud Build, Cloud Run, Artifact Registry)
2. Build and deploy the backend service
3. Build and deploy the frontend service with backend URL
4. Output the URLs for both services

### Manual Deployment

#### Deploy Backend

```bash
gcloud run deploy cokeeper-backend \
    --source ./backend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2
```

#### Deploy Frontend

```bash
# Get backend URL first
BACKEND_URL=$(gcloud run services describe cokeeper-backend --region us-central1 --format 'value(status.url)')

# Deploy frontend
gcloud run deploy cokeeper-frontend \
    --source ./frontend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8501 \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}"
```

## Project Structure

```
co-keeper-run/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── main.py
│   ├── ml_pipeline_qb.py
│   ├── ml_pipeline_xero.py
│   ├── requirements.txt
│   └── models/
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── app.py
│   └── requirements.txt
├── docker-compose.yml
├── deploy-cloud-run.sh
├── build-docker.sh
└── README.md
```

## Environment Variables

### Backend
- `PORT`: Server port (default: 8000)
- `ENVIRONMENT`: Environment name (development/production)

### Frontend
- `PORT`: Server port (default: 8501)
- `BACKEND_URL`: Backend API URL (required)

## API Endpoints

### Backend (FastAPI)

- `GET /`: Health check
- `POST /train/quickbooks`: Train QuickBooks model
- `POST /predict/quickbooks`: Predict QuickBooks categories
- `POST /train/xero`: Train Xero model
- `POST /predict/xero`: Predict Xero categories
- `GET /docs`: Interactive API documentation (Swagger UI)

## Monitoring

### View Logs

```bash
# Frontend logs
gcloud run services logs read cokeeper-frontend --region us-central1

# Backend logs
gcloud run services logs read cokeeper-backend --region us-central1

# Follow logs in real-time
gcloud run services logs tail cokeeper-frontend --region us-central1
```

### View Service Details

```bash
# Frontend service info
gcloud run services describe cokeeper-frontend --region us-central1

# Backend service info
gcloud run services describe cokeeper-backend --region us-central1
```

## Scaling Configuration

Services are configured with:
- **Min Instances**: 0 (scales to zero when not in use)
- **Max Instances**: 10
- **Memory**: 2Gi
- **CPU**: 2
- **Timeout**: 300 seconds

Adjust these in `deploy-cloud-run.sh` as needed.

## Cost Optimization

Cloud Run pricing:
- Free tier: 2 million requests/month
- CPU and memory are billed per 100ms of use
- No charges when services are scaled to zero

Tips:
- Services scale to zero automatically when not in use
- First request after scaling to zero may have cold start latency (~10-30s)
- Consider setting min-instances=1 for production if you need instant response

## Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Ensure all dependencies are in requirements.txt
- Check .dockerignore isn't excluding necessary files

### Service Doesn't Start
- Check logs: `gcloud run services logs read <service-name>`
- Verify port configuration matches Dockerfile
- Check environment variables are set correctly

### Frontend Can't Connect to Backend
- Verify BACKEND_URL environment variable is set
- Check CORS configuration in backend/main.py
- Ensure backend service allows unauthenticated access

## Development

### Testing Locally

```bash
# Start services
docker-compose up

# Run backend tests
docker-compose exec backend pytest

# Check backend health
curl http://localhost:8000/

# Access frontend
open http://localhost:8501
```

### Making Changes

1. Update code in `backend/` or `frontend/`
2. Test locally with docker-compose
3. Deploy to Cloud Run: `./deploy-cloud-run.sh`

## Security Notes

- Both services currently allow unauthenticated access
- For production, consider implementing:
  - Cloud Run IAM authentication
  - API keys
  - OAuth 2.0
  - VPC networking for service-to-service communication

## Support

For issues or questions:
1. Check Cloud Run logs
2. Review GCP quotas
3. Verify billing is enabled
4. Check service status in GCP Console

## License

[Your License Here]
