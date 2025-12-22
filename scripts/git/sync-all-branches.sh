#!/usr/bin/env bash
# ==============================================================================
# sync-all-branches.sh
# Sincroniza o repositório local, main e todas as branches de trabalho
# ==============================================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir mensagens
log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# ==============================================================================
# 1. ATUALIZAR REPOSITÓRIO LOCAL
# ==============================================================================
log_info "Atualizando repositório local..."

# Fetch de todas as alterações remotas
git fetch --all --prune
log_success "Repositório local atualizado com fetch --all"

# ==============================================================================
# 2. ATUALIZAR BRANCH MAIN
# ==============================================================================
log_info "Atualizando branch main..."

# Guardar a branch atual
CURRENT_BRANCH=$(git branch --show-current)
log_info "Branch atual: $CURRENT_BRANCH"

# Se não estiver na main, mudar para ela
if [ "$CURRENT_BRANCH" != "main" ]; then
    git checkout main
    log_success "Mudado para branch main"
fi

# Pull das últimas alterações
git pull origin main
log_success "Branch main atualizada"

# ==============================================================================
# 3. ATUALIZAR BRANCHES DE TRABALHO (cli e api)
# ==============================================================================

# Verificar se as branches existem localmente
BRANCHES_TO_UPDATE=("cli" "api")

for branch in "${BRANCHES_TO_UPDATE[@]}"; do
    log_info "Processando branch: $branch"

    # Verificar se a branch existe localmente
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        log_info "Branch $branch existe localmente"

        # Mudar para a branch
        git checkout "$branch"
        log_success "Mudado para branch $branch"

        # Pull das alterações remotas
        if git pull origin "$branch"; then
            log_success "Branch $branch atualizada do remoto"
        else
            log_warning "Não foi possível fazer pull da branch $branch (pode não ter upstream)"
        fi

        # Merge da main na branch
        log_info "Fazendo merge da main em $branch..."
        if git merge main --no-edit; then
            log_success "Merge da main em $branch concluído"
        else
            log_error "Conflito ao fazer merge da main em $branch!"
            log_warning "Resolva os conflitos manualmente e execute:"
            log_warning "  git merge --continue"
            log_warning "  git push origin $branch"
            exit 1
        fi

        # Push das alterações
        if git push origin "$branch"; then
            log_success "Branch $branch enviada para o remoto"
        else
            log_warning "Não foi possível fazer push da branch $branch"
        fi

    else
        log_warning "Branch $branch não existe localmente"

        # Verificar se existe no remoto
        if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
            log_info "Branch $branch existe no remoto. Criando localmente..."
            git checkout -b "$branch" "origin/$branch"
            log_success "Branch $branch criada localmente a partir do remoto"

            # Merge da main
            log_info "Fazendo merge da main em $branch..."
            if git merge main --no-edit; then
                log_success "Merge da main em $branch concluído"
                git push origin "$branch"
                log_success "Branch $branch enviada para o remoto"
            else
                log_error "Conflito ao fazer merge!"
                exit 1
            fi
        else
            log_warning "Branch $branch não existe nem localmente nem no remoto"
        fi
    fi

    echo ""
done

# ==============================================================================
# 4. VOLTAR PARA A BRANCH ORIGINAL
# ==============================================================================
if [ "$CURRENT_BRANCH" != "main" ]; then
    git checkout "$CURRENT_BRANCH"
    log_success "Retornado para branch original: $CURRENT_BRANCH"
fi

# ==============================================================================
# RESUMO
# ==============================================================================
echo ""
log_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Sincronização completa!"
log_success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_info "Status das branches:"
git branch -vv

echo ""
log_info "Commits recentes:"
git log --oneline --all --graph -10
