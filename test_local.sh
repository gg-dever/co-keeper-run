#!/bin/bash

# Local testing script for CoKeeper deployment

echo "🧪 Testing CoKeeper locally before cloud deployment"
echo "=================================================="

# Kill any existing processes on ports 8000 and 8501
echo ""
echo "📌 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
echo ""
echo "🚀 Starting backend on http://localhost:8000..."
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..

# Wait for backend to start
echo ""
echo "⏳ Waiting for backend to start..."
sleep 3

# Test backend health
echo ""
echo "🔍 Testing backend health endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool || echo "❌ Backend health check failed"

# Start frontend
echo ""
echo "🚀 Starting frontend on http://localhost:8501..."
cd frontend
BACKEND_URL=http://localhost:8000 streamlit run app.py --server.port=8501 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

# Wait for frontend to start
echo ""
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "✅ Local services running:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:8501"
echo ""
echo "📝 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "🧪 Test by uploading a Xero CSV at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both services"

# Keep script running
wait
