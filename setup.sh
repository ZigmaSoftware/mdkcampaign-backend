#!/bin/bash
# Setup script for Campaign OS Backend

set -e

echo "🚀 Campaign OS Backend Setup"
echo "============================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python --version

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your database credentials${NC}"
fi

# Check for MariaDB/MySQL
echo -e "${BLUE}Checking for MariaDB/MySQL...${NC}"
if ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}⚠️  MariaDB/MySQL client not found${NC}"
    echo "Install MySQL: sudo apt-get install mysql-client-core-8.0"
fi

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies with uv...${NC}"
uv sync

# Run migrations
echo -e "${BLUE}Running Django migrations...${NC}"
python manage.py migrate

# Create superuser
echo -e "${BLUE}Creating superuser...${NC}"
python manage.py createsuperuser

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env with your database credentials"
echo "2. Run: python manage.py runserver"
echo "3. Visit: http://localhost:8000/api/docs/"
