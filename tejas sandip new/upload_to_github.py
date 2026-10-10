"""
upload_to_github.py
-------------------
Automatic uploader for GitHub repository using standard GitHub REST API.
No local git installation required! Works directly over HTTPS with Python standard library.

Usage:
    python upload_to_github.py
    or
    python upload_to_github.py --token YOUR_GITHUB_TOKEN
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import argparse

REPO_OWNER = "nagaretejas077"
REPO_NAME = "obejct-detection-system"
BRANCH = "main"

# Files to upload to the repository
FILES_TO_UPLOAD = [
    "main.py",
    "detector.py",
    "database.py",
    "ui.py",
    "database_schema.sql",
    "requirements.txt",
    "README.md",
    ".env.example",
    ".gitignore",
    "MEDIUM_ARTICLE.md",
    "DEMO_VIDEO_GUIDE.md",
    "SUBMISSION_CHECKLIST.md",
]


def get_file_sha(filepath, token):
    """Checks if file already exists in the repo to obtain its sha for updating."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filepath}?ref={BRANCH}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Python-GitHub-Uploader")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise e
    return None


def upload_file(filepath, token):
    """Uploads a single file to GitHub repository via REST API."""
    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {filepath}")
        return False

    with open(filepath, "rb") as f:
        content_bytes = f.read()

    encoded_content = base64.b64encode(content_bytes).decode("utf-8")
    sha = get_file_sha(filepath, token)

    payload = {
        "message": f"Upload {filepath} for Assignment 5",
        "content": encoded_content,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filepath}"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Python-GitHub-Uploader")

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                action = "Updated" if sha else "Created"
                print(f" [✔] {action}: {filepath}")
                return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f" [✖] Error uploading {filepath} (HTTP {e.code}): {err_msg}")
        return False
    except Exception as e:
        print(f" [✖] Exception uploading {filepath}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload project files to GitHub repository automatically.")
    parser.add_argument("--token", type=str, default="", help="GitHub Personal Access Token (classic or fine-grained)")
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN", "")

    if not token:
        print("\n=======================================================")
        print("  Automatic GitHub Repository Uploader")
        print("  Target: https://github.com/nagaretejas077/obejct-detection-system")
        print("=======================================================\n")
        print("To push to GitHub automatically, GitHub requires an authorized access token.")
        print("Generate a token in 10 seconds here: https://github.com/settings/tokens/new")
        print("Permissions required: Check the 'repo' scope checkbox.\n")
        token = input("Paste your GitHub Token (starts with ghp_ or github_pat_): ").strip()

    if not token:
        print("\n[ERROR] No token provided. Upload aborted.")
        sys.exit(1)

    print(f"\n[*] Connecting to https://github.com/{REPO_OWNER}/{REPO_NAME}...")
    success_count = 0
    for f in FILES_TO_UPLOAD:
        if upload_file(f, token):
            success_count += 1

    print(f"\n[DONE] Successfully uploaded {success_count}/{len(FILES_TO_UPLOAD)} files to:")
    print(f" 👉 https://github.com/{REPO_OWNER}/{REPO_NAME}\n")


if __name__ == "__main__":
    main()
