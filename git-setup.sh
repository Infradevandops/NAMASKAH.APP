#!/bin/bash

# Git setup script for namaskah
# This script initializes the git repository and prepares it for pushing to GitHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

# Repository URL
REPO_URL="https://github.com/Infradevandops/namaskah.git"

print_status "Setting up Git repository for namaskah..."

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    print_status "Initializing Git repository..."
    git init
    print_success "Git repository initialized"
else
    print_status "Git repository already exists"
fi

# Add remote origin if not already added
if ! git remote get-url origin &> /dev/null; then
    print_status "Adding remote origin..."
    git remote add origin $REPO_URL
    print_success "Remote origin added: $REPO_URL"
else
    print_status "Remote origin already exists"
    current_origin=$(git remote get-url origin)
    if [ "$current_origin" != "$REPO_URL" ]; then
        print_warning "Current origin: $current_origin"
        print_warning "Expected origin: $REPO_URL"
        print_status "Updating remote origin..."
        git remote set-url origin $REPO_URL
        print_success "Remote origin updated"
    fi
fi

# Check if .env file exists and warn about it
if [ -f ".env" ]; then
    print_warning ".env file detected. Make sure it's in .gitignore and doesn't contain real API keys!"
fi

# Add all files to staging
print_status "Adding files to Git staging area..."
git add .

# Check if there are any changes to commit
if git diff --staged --quiet; then
    print_warning "No changes to commit"
else
    # Commit changes
    print_status "Committing changes..."
    
    # Check if this is the first commit
    if ! git rev-parse --verify HEAD &> /dev/null; then
        commit_message="Initial commit: namaskah communication platform

- FastAPI application with Twilio, TextVerified, and Groq integration
- Docker containerization with multi-service setup
- Comprehensive API endpoints for SMS and verification
- AI-powered conversation assistance
- Production-ready configuration with Nginx and PostgreSQL
- Complete CI/CD pipeline with GitHub Actions
- Documentation and development tools"
    else
        commit_message="Update: Latest changes to namaskah

- Updated application code and configuration
- Enhanced documentation and setup scripts
- Improved Docker and deployment configuration"
    fi
    
    git commit -m "$commit_message"
    print_success "Changes committed"
fi

# Check current branch
current_branch=$(git branch --show-current)
print_status "Current branch: $current_branch"

# Create main branch if we're on master
if [ "$current_branch" = "master" ]; then
    print_status "Renaming master branch to main..."
    git branch -m main
    current_branch="main"
    print_success "Branch renamed to main"
fi

# Push to GitHub
print_status "Pushing to GitHub repository..."
print_warning "You may be prompted for GitHub credentials..."

if git push -u origin $current_branch; then
    print_success "Successfully pushed to GitHub!"
    print_success "Repository URL: $REPO_URL"
    print_status "You can now:"
    echo "  - View your repository at: $REPO_URL"
    echo "  - Clone it elsewhere with: git clone $REPO_URL"
    echo "  - Set up CI/CD by configuring GitHub Actions secrets"
else
    print_error "Failed to push to GitHub"
    print_status "This might be due to:"
    echo "  - Authentication issues (check your GitHub credentials)"
    echo "  - Repository doesn't exist or you don't have access"
    echo "  - Network connectivity issues"
    echo ""
    print_status "To push manually later, run:"
    echo "  git push -u origin $current_branch"
    exit 1
fi

# Display next steps
print_success "Git setup complete!"
echo ""
print_status "Next steps:"
echo "1. Configure GitHub Actions secrets for CI/CD:"
echo "   - DOCKER_USERNAME: Your Docker Hub username"
echo "   - DOCKER_PASSWORD: Your Docker Hub password/token"
echo ""
echo "2. Set up branch protection rules on GitHub:"
echo "   - Require pull request reviews"
echo "   - Require status checks to pass"
echo "   - Require branches to be up to date"
echo ""
echo "3. Configure deployment environments:"
echo "   - Add production environment secrets"
echo "   - Set up deployment targets"
echo ""
echo "4. Start developing:"
echo "   - Create feature branches: git checkout -b feature/your-feature"
echo "   - Make changes and create pull requests"
echo "   - Use the CI/CD pipeline for automated testing and deployment"