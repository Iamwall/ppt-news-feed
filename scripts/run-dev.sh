#!/bin/bash
# Development run script for Unix/Linux/macOS
# Usage: ./scripts/run-dev.sh

echo "🔬 Science Digest - Development Mode"
echo "===================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start database and Redis
echo -e "\n📦 Starting database and Redis..."
docker-compose up -d db redis

# Wait for database
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Function to cleanup
cleanup() {
    echo -e "\n🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    docker-compose down
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "\n🐍 Starting backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "⚛️  Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n✅ Services starting..."
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop all services\n"

# Wait for processes
wait
