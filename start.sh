#!/bin/bash

echo "🚀 Starting Codebase Ingestion System"
echo "====================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please make sure Docker is up to date."
    exit 1
fi

echo "📦 Starting services with Docker Compose..."
docker compose up -d

echo "⏳ Waiting for services to initialize..."
sleep 10

echo "🔍 Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ All services are healthy!"
        break
    fi
    echo "⏳ Waiting for services... (attempt $i/30)"
    sleep 10
done

if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Services failed to start properly. Check logs with:"
    echo "   docker compose logs"
    exit 1
fi

echo ""
echo "🎉 System is ready!"
echo "=================="
echo "🌐 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "🧪 Run tests: python test_system.py"
echo "📊 View logs: docker compose logs -f"
echo "🛑 Stop services: docker compose down"
echo ""
echo "📋 Quick API Examples:"
echo "  # List projects"
echo "  curl http://localhost:8000/projects/"
echo ""
echo "  # Create project from Git"
echo "  curl -X POST http://localhost:8000/projects/ \\"
echo "    -F 'name=my-project' \\"
echo "    -F 'description=Test project' \\"
echo "    -F 'repo_url=https://github.com/octocat/Hello-World.git' \\"
echo "    -F 'language=python'"
echo ""
echo "  # Search code"
echo "  curl -X POST http://localhost:8000/search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"hello world function\", \"limit\": 5}'"
