#!/usr/bin/env bash
# ==============================================================================
# update-branches.sh
# Atualiza as branches cli e api com as alterações da main
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Guardar a branch atual
CURRENT_BRANCH=$(git branch --show-current)

# Primeiro atualizar a main
echo -e "${BLUE}ℹ${NC} Atualizando main primeiro..."
git checkout main
git pull origin main
echo -e "${GREEN}✓${NC} Main atualizada"
echo ""

# Branches para atualizar
BRANCHES=("cli" "api")

for branch in "${BRANCHES[@]}"; do
    echo -e "${BLUE}ℹ${NC} Processando branch: $branch"

    # Verificar se a branch existe
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        # Branch existe localmente
        git checkout "$branch"

        # Pull do remoto
        echo -e "${BLUE}ℹ${NC} Atualizando $branch do remoto..."
        git pull origin "$branch" || echo -e "${YELLOW}⚠${NC} Sem upstream remoto"

        # Merge da main
        echo -e "${BLUE}ℹ${NC} Fazendo merge da main em $branch..."
        if git merge main --no-edit; then
            echo -e "${GREEN}✓${NC} Merge concluído com sucesso"

            # Push para o remoto
            git push origin "$branch"
            echo -e "${GREEN}✓${NC} Branch $branch atualizada e enviada para o remoto"
        else
            echo -e "${RED}✗${NC} Conflito detectado! Resolva manualmente:"
            echo -e "  ${YELLOW}git merge --continue${NC}"
            echo -e "  ${YELLOW}git push origin $branch${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} Branch $branch não existe localmente"

        # Verificar se existe no remoto
        if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
            echo -e "${BLUE}ℹ${NC} Criando $branch a partir do remoto..."
            git checkout -b "$branch" "origin/$branch"

            # Merge da main
            git merge main --no-edit
            git push origin "$branch"
            echo -e "${GREEN}✓${NC} Branch $branch criada e atualizada"
        else
            echo -e "${YELLOW}⚠${NC} Branch $branch não existe no remoto"
        fi
    fi

    echo ""
done

# Voltar para a branch original
git checkout "$CURRENT_BRANCH"
echo -e "${GREEN}✓${NC} Retornado para branch $CURRENT_BRANCH"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Todas as branches atualizadas!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
