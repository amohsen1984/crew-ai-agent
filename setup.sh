#!/bin/bash

# Setup script for CrewAI Feedback Agent
# Creates virtual environment, installs dependencies, and runs docker-compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}🚀 Setting up CrewAI Feedback Agent...${NC}\n"

# Check Python version (requires 3.11+)
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is not installed or not in PATH${NC}"
    echo -e "${YELLOW}   Please install Python 3.11 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ -z "$PYTHON_MAJOR" ] || [ -z "$PYTHON_MINOR" ]; then
    echo -e "${YELLOW}⚠️  Warning: Could not determine Python version, continuing anyway...${NC}\n"
elif [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}❌ Error: Python 3.11+ is required. Found Python $PYTHON_VERSION${NC}"
    echo -e "${YELLOW}   Please install Python 3.11 or higher${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python version check passed ($PYTHON_VERSION)${NC}\n"
fi

# Step 1: Create backend virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}📦 Creating backend virtual environment...${NC}"
    python3 -m venv backend/venv
    if [ ! -f "backend/venv/bin/activate" ]; then
        echo -e "${RED}❌ Error: Failed to create backend virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Backend virtual environment created${NC}\n"
else
    echo -e "${GREEN}✅ Backend virtual environment already exists${NC}\n"
fi

# Step 2: Create frontend virtual environment if it doesn't exist
if [ ! -d "frontend/venv" ]; then
    echo -e "${YELLOW}📦 Creating frontend virtual environment...${NC}"
    python3 -m venv frontend/venv
    if [ ! -f "frontend/venv/bin/activate" ]; then
        echo -e "${RED}❌ Error: Failed to create frontend virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Frontend virtual environment created${NC}\n"
else
    echo -e "${GREEN}✅ Frontend virtual environment already exists${NC}\n"
fi

# Step 3: Install backend dependencies
if [ -f "backend/requirements.txt" ]; then
    echo -e "${YELLOW}📦 Installing backend dependencies...${NC}"
    source backend/venv/bin/activate
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    deactivate
    echo -e "${GREEN}✅ Backend dependencies installed${NC}\n"
else
    echo -e "${RED}❌ Error: backend/requirements.txt not found${NC}"
    exit 1
fi

# Step 4: Install frontend dependencies
if [ -f "frontend/requirements.txt" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    source frontend/venv/bin/activate
    pip install --upgrade pip
    pip install -r frontend/requirements.txt
    deactivate
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}\n"
else
    echo -e "${RED}❌ Error: frontend/requirements.txt not found${NC}"
    exit 1
fi

# Step 5: Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}📝 Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env file and add your OPENAI_API_KEY${NC}\n"
    else
        echo -e "${YELLOW}⚠️  Warning: .env file not found and no .env.example exists${NC}"
        echo -e "${YELLOW}   Creating a basic .env file...${NC}"
        cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
MODEL_NAME=gpt-4

# Verbose Logging
VERBOSE=false
EOF
        echo -e "${GREEN}✅ Basic .env file created${NC}"
        echo -e "${RED}⚠️  IMPORTANT: Please edit .env file and add your OPENAI_API_KEY${NC}\n"
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}\n"
fi

# Step 6: Verify .env has required variables
if grep -q "your_openai_api_key_here" .env 2>/dev/null || ! grep -q "OPENAI_API_KEY=" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Please ensure OPENAI_API_KEY is set in .env file${NC}\n"
fi

# Step 7: Run docker-compose
echo -e "${GREEN}🐳 Starting Docker Compose...${NC}\n"
echo -e "${YELLOW}   This will build and start both backend and frontend services${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop the services${NC}\n"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed or not in PATH${NC}"
    echo -e "${YELLOW}   Please install Docker Desktop: https://www.docker.com/products/docker-desktop${NC}"
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
# Note: docker-compose automatically reads .env file from the same directory
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    docker compose up --build
elif command -v docker-compose &> /dev/null; then
    docker-compose up --build
else
    echo -e "${RED}❌ Error: docker-compose command not found${NC}"
    exit 1
fi

