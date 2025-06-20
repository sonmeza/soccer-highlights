#!/usr/bin/env python3
"""
Automated GitHub repository creation and file upload script
This script creates a GitHub repository and uploads files using the GitHub API
"""

import requests
import base64
import json
import os
import getpass
from pathlib import Path

class GitHubUploader:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = None
        self.username = "sonmeza"
        self.repo_name = "soccer-analysis-app"
        
    def authenticate(self):
        """Authenticate with GitHub using personal access token"""
        print("GitHub Authentication Required")
        print("You need a GitHub Personal Access Token with 'repo' permissions")
        print("Create one at: https://github.com/settings/tokens")
        print()
        
        self.token = getpass.getpass("Enter your GitHub Personal Access Token: ")
        
        # Test authentication
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(f"{self.base_url}/user", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            self.username = user_data["login"]
            print(f"Successfully authenticated as: {self.username}")
            return True
        else:
            print("Authentication failed. Please check your token.")
            return False
    
    def create_repository(self):
        """Create a new GitHub repository"""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "name": self.repo_name,
            "description": "Soccer Analysis App with video processing and overlay advertisements",
            "private": False,
            "auto_init": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True
        }
        
        response = requests.post(f"{self.base_url}/user/repos", 
                               headers=headers, json=data)
        
        if response.status_code == 201:
            repo_data = response.json()
            print(f"Repository created: {repo_data['html_url']}")
            return True
        elif response.status_code == 422:
            print("Repository already exists. Continuing with upload...")
            return True
        else:
            print(f"Failed to create repository: {response.json()}")
            return False
    
    def upload_file(self, file_path, github_path=None):
        """Upload a single file to GitHub repository"""
        if github_path is None:
            github_path = file_path
            
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return False
        
        data = {
            "message": f"Add {github_path}",
            "content": content
        }
        
        url = f"{self.base_url}/repos/{self.username}/{self.repo_name}/contents/{github_path}"
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print(f"Uploaded: {github_path}")
            return True
        else:
            print(f"Failed to upload {github_path}: {response.json()}")
            return False
    
    def upload_all_files(self):
        """Upload all project files to GitHub"""
        files_to_upload = [
            "app.py",
            "requirements.txt",
            "README.md",
            "replit.md",
            "Procfile",
            "run_app.py",
            "GITHUB_SETUP.md",
            "QUICK_GITHUB_PUSH.md",
            ".gitignore",
            "install_dependencies.py",
            ".streamlit/config.toml",
            ".devcontainer/devcontainer.json",
            ".devcontainer/setup.sh"
        ]
        
        uploaded_count = 0
        for file_path in files_to_upload:
            if os.path.exists(file_path):
                if self.upload_file(file_path):
                    uploaded_count += 1
            else:
                print(f"File not found: {file_path}")
        
        print(f"\nUploaded {uploaded_count} files successfully!")
        return uploaded_count > 0
    
    def run(self):
        """Main execution flow"""
        print("Soccer Analysis App - GitHub Upload Tool")
        print("=" * 50)
        
        if not self.authenticate():
            return False
        
        if not self.create_repository():
            return False
        
        if not self.upload_all_files():
            return False
        
        repo_url = f"https://github.com/{self.username}/{self.repo_name}"
        print(f"\nSuccess! Your repository is ready:")
        print(f"Repository: {repo_url}")
        print(f"Codespaces: {repo_url}/codespaces")
        print(f"Deploy to Streamlit: https://share.streamlit.io")
        
        return True

def main():
    uploader = GitHubUploader()
    success = uploader.run()
    
    if not success:
        print("\nAlternative options:")
        print("1. Download files manually from Replit")
        print("2. Use GitHub Desktop application")
        print("3. Follow the manual upload guide in QUICK_GITHUB_PUSH.md")

if __name__ == "__main__":
    main()