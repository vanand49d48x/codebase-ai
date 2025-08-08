#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}CodebaseAI Test Runner${NC}"
echo -e "${BLUE}================================${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    exit 1
fi

# Check if requests module is available
if ! python3 -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}⚠ Installing requests module...${NC}"
    pip3 install requests
fi

# Check if system is running
echo -e "${BLUE}Checking if system is running...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ System is not running!${NC}"
    echo -e "${YELLOW}Please start the system first with: ./start.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ System is running, starting tests...${NC}"

# Run the test suite
python3 tests/test_system.py

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
