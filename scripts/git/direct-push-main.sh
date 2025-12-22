#!/bin/bash
# scripts/git/direct-push-main.sh
# Protocolo automatizado para push direto na branch main
# Baseado em: docs/guides/DIRECT_PUSH_PROTOCOL.md
#
# Uso: ./scripts/git/direct-push-main.sh
# Executa após ter feito commit local na main

set -e  # Exit on error
set -o pipefail  # Fail on pipe errors

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

echo ""
print_step "🚀 Direct Push to Main Protocol v1.0.0"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Verify we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    print_error "Not on main branch (current: $CURRENT_BRANCH)"
    print_info "Switch to main with: git checkout main"
    exit 1
fi

# Step 1: Validate changes
print_step "🔍 Step 1/4: Validating changes"
echo "Running quality checks..."
echo ""

if ! make validate; then
    print_error "Validation failed. Fix errors and try again."
    exit 1
fi

print_success "All validations passed"
echo ""

# Step 2: Push to origin/main
print_step "📤 Step 2/4: Pushing to origin/main"
echo "Pushing commits to remote..."
echo ""

if ! git push origin main; then
    print_error "Failed to push to origin/main"
    print_info "Check for conflicts or network issues"
    exit 1
fi

print_success "Successfully pushed to origin/main"
echo ""

# Step 3: Sync local with remote
print_step "🔄 Step 3/4: Syncing local with remote"
echo "Pulling latest changes from origin/main..."
echo ""

if ! git pull origin main; then
    print_warning "Pull failed. There might be conflicts."
    print_info "Resolve manually and run: git pull origin main"
    exit 1
fi

print_success "Local repository synchronized"
echo ""

# Step 4: Clean Git graph
print_step "🧹 Step 4/4: Cleaning Git graph"
echo "  → Pruning remote refs..."
git fetch --prune

echo "  → Running garbage collection (auto)..."
git gc --auto

print_success "Git graph cleaned"
echo ""

# Final status
print_step "📊 Final Status"
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Status:"
git status --short

if [ -z "$(git status --porcelain)" ]; then
    print_success "Working tree clean"
else
    print_warning "There are uncommitted changes:"
    git status --porcelain
fi

echo ""
echo "Recent commits:"
git log --oneline -3

echo ""
print_step "🎉 Direct push completed successfully!"
echo ""

# Summary
print_info "What was done:"
echo "  ✓ Code validated (ruff, mypy, pytest)"
echo "  ✓ Changes pushed to origin/main"
echo "  ✓ Local repository synchronized"
echo "  ✓ Git graph cleaned"
echo ""

exit 0
