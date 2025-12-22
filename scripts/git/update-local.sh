#!/usr/bin/env bash
# ==============================================================================
# update-local.sh
# Atualiza o repositório local com todas as mudanças remotas
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}ℹ${NC} Atualizando repositório local..."

# Fetch de todas as alterações remotas incluindo tags
git fetch --all --prune --tags

echo -e "${GREEN}✓${NC} Repositório local atualizado!"
echo ""
echo "Status das branches:"
git branch -vv
