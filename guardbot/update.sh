#!/bin/bash
# ===============================================
# GuardBot Quick Update Script
# ===============================================
# Updates and restarts the bot on server
# ===============================================

set -e

SERVER="37.233.85.194"
USER="root"
DEPLOY_PATH="/opt/guardbot"
BRANCH="main"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Updating GuardBot...${NC}"

# Update code
ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "cd ${DEPLOY_PATH} && git pull origin ${BRANCH}"

# Restart bot
ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "cd ${DEPLOY_PATH} && docker compose restart"

echo -e "${GREEN}✓ Bot updated and restarted!${NC}"

# Show logs
echo -e "\n${YELLOW}Recent logs:${NC}"
ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "cd ${DEPLOY_PATH} && docker compose logs --tail=20"
