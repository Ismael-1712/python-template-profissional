#!/bin/bash
# scripts/git/post-pr-cleanup.sh
# Protocolo automatizado para limpeza após Pull Request Merge
# Baseado em: docs/guides/POST_PR_MERGE_PROTOCOL.md
#
# Uso: ./scripts/git/post-pr-cleanup.sh <branch-name>
# Exemplo: ./scripts/git/post-pr-cleanup.sh feat/P010-vector-bridge

set -e  # Exit on error
set -o pipefail  # Fail on pipe errors

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Validate arguments
if [ $# -eq 0 ]; then
    print_error "Branch name required"
    echo "Usage: $0 <branch-name>"
    echo "Example: $0 feat/P010-vector-bridge"
    exit 1
fi

BRANCH_NAME=$1

echo ""
print_step "📋 Post-PR Cleanup Protocol v1.0.0"
echo "Branch: $BRANCH_NAME"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 0: Check for uncommitted changes
print_step "🔍 Step 0/5: Checking for uncommitted changes"
if [ -n "$(git status --porcelain)" ]; then
    print_error "Working tree has uncommitted changes. Please commit or stash them first."
    echo ""
    echo "Uncommitted changes:"
    git status --short
    echo ""
    echo "💡 Suggested actions:"
    echo "   1. Commit changes: git add . && git commit -m 'your message'"
    echo "   2. Stash changes:  git stash"
    echo "   3. Discard changes: git restore <file>"
    exit 1
fi
print_success "Working tree clean"
echo ""

# Step 1: Sync main with remote
print_step "📥 Step 1/6: Syncing main with origin"
if ! git checkout main; then
    print_error "Failed to checkout main branch"
    exit 1
fi

if ! git pull origin main; then
    print_error "Failed to pull from origin/main"
    exit 1
fi
print_success "Main branch updated"
echo ""

# Step 2: Delete local branch
print_step "🗑️  Step 2/6: Deleting local branch"
if git branch -d "$BRANCH_NAME" 2>/dev/null; then
    print_success "Local branch '$BRANCH_NAME' deleted"
else
    print_warning "Could not delete local branch (may not exist or has unmerged changes)"
fi
echo ""

# Step 3: Delete remote branch (if exists)
print_step "🌐 Step 3/6: Deleting remote branch"
if git push origin --delete "$BRANCH_NAME" 2>/dev/null; then
    print_success "Remote branch deleted"
else
    print_warning "Remote branch does not exist (already deleted by GitHub)"
fi
echo ""

# Step 4: Update development branches
print_step "🔄 Step 4/6: Updating development branches"
for branch in cli api; do
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
        echo "  → Updating $branch..."
        if git checkout "$branch" && git pull origin "$branch"; then
            print_success "Branch '$branch' updated"
        else
            print_warning "Failed to update branch '$branch'"
        fi
    else
        echo "  → Branch '$branch' does not exist (skipping)"
    fi
done

# Return to main
git checkout main
echo ""

# Step 5: Clean Git graph
print_step "🧹 Step 5/6: Cleaning Git graph"
echo "  → Pruning remote refs..."
git fetch --prune

echo "  → Running garbage collection..."
git gc --aggressive --prune=now

print_success "Git graph cleaned"
echo ""

# Final validation
print_step "✅ Validation"
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Status:"
git status --short

if [ -z "$(git status --porcelain)" ]; then
    print_success "Working tree clean"
else
    print_warning "There are uncommitted changes"
fi

echo ""
echo "Recent commits:"
git log --oneline -3

echo ""
print_step "🎉 Cleanup completed successfully!"
echo ""

exit 0
