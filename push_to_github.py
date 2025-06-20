#!/usr/bin/env python3
"""
Script to push Soccer Analysis App to GitHub from Replit
This script will guide you through creating a repository and pushing code
"""

import subprocess
import os
import sys
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command and return the result"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False, result.stderr
        print(f"Success: {description}")
        if result.stdout.strip():
            print(f"Output: {result.stdout}")
        return True, result.stdout
    except Exception as e:
        print(f"Exception: {e}")
        return False, str(e)

def setup_git_config():
    """Set up Git configuration"""
    print("\n=== Setting up Git Configuration ===")
    
    # Check if Git is already configured
    success, output = run_command("git config --global user.name")
    if not success or not output.strip():
        name = input("Enter your Git username: ")
        run_command(f'git config --global user.name "{name}"')
    
    success, output = run_command("git config --global user.email")
    if not success or not output.strip():
        email = input("Enter your Git email: ")
        run_command(f'git config --global user.email "{email}"')
    
    print("Git configuration complete!")

def prepare_files():
    """Prepare files for GitHub upload"""
    print("\n=== Preparing Files ===")
    
    # Create requirements.txt from github_requirements.txt
    if os.path.exists("github_requirements.txt"):
        run_command("cp github_requirements.txt requirements.txt", "Created requirements.txt")
    
    # Make scripts executable
    run_command("chmod +x run_app.py", "Made run_app.py executable")
    run_command("chmod +x .devcontainer/setup.sh", "Made setup script executable")
    
    # Remove temporary files
    files_to_remove = ["video_overlay_fix.py", "github_requirements.txt"]
    for file in files_to_remove:
        if os.path.exists(file):
            run_command(f"rm {file}", f"Removed {file}")
    
    print("Files prepared for GitHub!")

def initialize_repo():
    """Initialize Git repository"""
    print("\n=== Initializing Git Repository ===")
    
    # Initialize git if not already done
    if not os.path.exists(".git"):
        run_command("git init", "Initialized Git repository")
    
    # Add all files
    run_command("git add .", "Added all files to Git")
    
    # Create initial commit
    run_command('git commit -m "Initial commit - Soccer Analysis App with video overlay advertisements"', "Created initial commit")
    
    print("Git repository initialized!")

def push_to_github():
    """Push to GitHub repository"""
    print("\n=== GitHub Repository Setup ===")
    print("You have two options:")
    print("1. Create a new repository on GitHub first (recommended)")
    print("2. Use an existing repository")
    print()
    
    repo_url = input("Enter your GitHub repository URL (e.g., https://github.com/username/soccer-analysis-app.git): ")
    
    if not repo_url:
        print("No repository URL provided. Please create a repository on GitHub first.")
        print("Go to: https://github.com/new")
        print("Repository name: soccer-analysis-app")
        print("Make it public, don't initialize with README")
        return False
    
    # Add remote origin
    run_command("git remote remove origin", "Removed existing origin (if any)")
    success, _ = run_command(f"git remote add origin {repo_url}", "Added GitHub remote")
    
    if not success:
        print("Failed to add remote. Please check the repository URL.")
        return False
    
    # Push to GitHub
    print("\nPushing to GitHub...")
    success, output = run_command("git push -u origin main", "Pushed to GitHub")
    
    if not success:
        # Try master branch if main fails
        print("Trying master branch...")
        success, output = run_command("git push -u origin master", "Pushed to GitHub (master)")
    
    if success:
        print(f"\n✅ Successfully pushed to GitHub!")
        print(f"Repository: {repo_url}")
        print(f"\nNext steps:")
        print(f"1. Visit your repository on GitHub")
        print(f"2. Enable GitHub Codespaces")
        print(f"3. Deploy to Streamlit Cloud: https://share.streamlit.io")
        return True
    else:
        print("Push failed. You may need to authenticate with GitHub.")
        print("Try using GitHub CLI: gh auth login")
        return False

def main():
    """Main execution function"""
    print("🏈 Soccer Analysis App - GitHub Push Tool")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("Error: app.py not found. Please run this script from the project directory.")
        sys.exit(1)
    
    # Setup Git configuration
    setup_git_config()
    
    # Prepare files
    prepare_files()
    
    # Initialize repository
    initialize_repo()
    
    # Push to GitHub
    if push_to_github():
        print("\n🎉 Your Soccer Analysis App is now on GitHub!")
        print("You can now use GitHub Codespaces for development.")
    else:
        print("\n❌ Push failed. Please check the error messages above.")
        print("You may need to:")
        print("1. Create the repository on GitHub first")
        print("2. Authenticate with GitHub (gh auth login)")
        print("3. Check your internet connection")

if __name__ == "__main__":
    main()