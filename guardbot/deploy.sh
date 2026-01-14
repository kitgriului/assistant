#!/bin/bash
# ===============================================
# GuardBot Deployment Script
# ===============================================
# Server: 37.233.85.194
# Repository: git@github.com:otg-tech/bots.git
# ===============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER="37.233.85.194"
USER="root"
REPO="git@github.com:otg-tech/bots.git"
DEPLOY_PATH="/opt/guardbot"
BRANCH="main"

echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}GuardBot Deployment Script${NC}"
echo -e "${GREEN}===============================================${NC}"

# Function to run command on server
run_remote() {
    ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "$1"
}

# Function to check if Docker is installed
check_docker() {
    echo -e "\n${YELLOW}Checking Docker installation...${NC}"
    if run_remote "command -v docker &> /dev/null"; then
        echo -e "${GREEN}✓ Docker is installed${NC}"
    else
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo -e "${YELLOW}Installing Docker...${NC}"
        run_remote "curl -fsSL https://get.docker.com | sh"
        run_remote "systemctl enable docker && systemctl start docker"
        echo -e "${GREEN}✓ Docker installed successfully${NC}"
    fi
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    echo -e "\n${YELLOW}Checking Docker Compose...${NC}"
    if run_remote "docker compose version &> /dev/null"; then
        echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    else
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        echo -e "${YELLOW}Installing Docker Compose plugin...${NC}"
        run_remote "apt-get update && apt-get install -y docker-compose-plugin"
        echo -e "${GREEN}✓ Docker Compose installed successfully${NC}"
    fi
}

# Function to clone or update repository
setup_repository() {
    echo -e "\n${YELLOW}Setting up repository...${NC}"
    
    if run_remote "[ -d ${DEPLOY_PATH} ]"; then
        echo -e "${YELLOW}Repository exists, updating...${NC}"
        run_remote "cd ${DEPLOY_PATH} && git fetch origin && git reset --hard origin/${BRANCH}"
        echo -e "${GREEN}✓ Repository updated${NC}"
    else
        echo -e "${YELLOW}Cloning repository...${NC}"
        run_remote "mkdir -p /opt && cd /opt && git clone ${REPO} guardbot"
        run_remote "cd ${DEPLOY_PATH} && git checkout ${BRANCH}"
        echo -e "${GREEN}✓ Repository cloned${NC}"
    fi
}

# Function to setup .env file
setup_env() {
    echo -e "\n${YELLOW}Setting up .env file...${NC}"
    
    # Copy local .env to server
    scp -o StrictHostKeyChecking=no .env ${USER}@${SERVER}:${DEPLOY_PATH}/.env
    echo -e "${GREEN}✓ .env file uploaded${NC}"
}

# Function to deploy bot
deploy_bot() {
    echo -e "\n${YELLOW}Deploying bot...${NC}"
    
    # Stop existing container
    echo -e "${YELLOW}Stopping existing containers...${NC}"
    run_remote "cd ${DEPLOY_PATH} && docker compose down || true"
    
    # Build and start
    echo -e "${YELLOW}Building Docker image...${NC}"
    run_remote "cd ${DEPLOY_PATH} && docker compose build"
    
    echo -e "${YELLOW}Starting bot...${NC}"
    run_remote "cd ${DEPLOY_PATH} && docker compose up -d"
    
    # Wait for container to start
    sleep 5
    
    # Check health
    echo -e "\n${YELLOW}Checking bot health...${NC}"
    if run_remote "cd ${DEPLOY_PATH} && docker compose ps | grep -q 'running'"; then
        echo -e "${GREEN}✓ Bot is running!${NC}"
    else
        echo -e "${RED}✗ Bot failed to start${NC}"
        echo -e "${YELLOW}Showing logs:${NC}"
        run_remote "cd ${DEPLOY_PATH} && docker compose logs --tail=50"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    echo -e "\n${YELLOW}Recent logs:${NC}"
    run_remote "cd ${DEPLOY_PATH} && docker compose logs --tail=20"
}

# Main deployment flow
main() {
    echo -e "\n${YELLOW}Starting deployment...${NC}"
    
    check_docker
    check_docker_compose
    setup_repository
    setup_env
    deploy_bot
    show_logs
    
    echo -e "\n${GREEN}===============================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo -e "\n${YELLOW}Useful commands:${NC}"
    echo -e "  View logs:    ssh ${USER}@${SERVER} 'cd ${DEPLOY_PATH} && docker compose logs -f'"
    echo -e "  Restart bot:  ssh ${USER}@${SERVER} 'cd ${DEPLOY_PATH} && docker compose restart'"
    echo -e "  Stop bot:     ssh ${USER}@${SERVER} 'cd ${DEPLOY_PATH} && docker compose down'"
    echo -e "  Check status: ssh ${USER}@${SERVER} 'cd ${DEPLOY_PATH} && docker compose ps'"
}

# Run main function
main
