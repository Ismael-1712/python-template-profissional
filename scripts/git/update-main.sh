#!/usr/bin/env bash
# ==============================================================================
# update-main.sh
# Atualiza a branch main com as últimas alterações do remoto
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}ℹ${NC} Atualizando branch main..."

# Guardar a branch atual
CURRENT_BRANCH=$(git branch --show-current)

# Se não estiver na main, mudar para ela
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠${NC} Mudando de $CURRENT_BRANCH para main..."
    git checkout main
fi

# Atualizar do remoto
git fetch origin main
git pull origin main

echo -e "${GREEN}✓${NC} Branch main atualizada!"

# Voltar para a branch original se não era main
if [ "$CURRENT_BRANCH" != "main" ]; then
    git checkout "$CURRENT_BRANCH"
    echo -e "${GREEN}✓${NC} Retornado para branch $CURRENT_BRANCH"
fi

echo ""
git log --oneline -5
