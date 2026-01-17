#!/bin/bash

echo "🚔 Starting Detective Evidence Management System..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    echo ""
fi

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
python3 -m pip install -q -r requirements.txt
echo ""

# Start Node.js server in background
echo "🚀 Starting Node.js Evidence Server (Port 3000)..."
npm start &
NODE_PID=$!

# Wait a moment for Node server to start
sleep 2

# Start Python AI Agent API in background
echo "🤖 Starting Python AI Agent API (Port 5000)..."
python3 agent_api.py &
PYTHON_PID=$!

# Wait a moment for Python server to start
sleep 2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Both servers are running!"
echo ""
echo "📡 Evidence Upload: http://localhost:3000"
echo "🤖 AI Case Analysis: http://localhost:3000/case-analysis.html"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $NODE_PID 2>/dev/null
    kill $PYTHON_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up trap to cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
