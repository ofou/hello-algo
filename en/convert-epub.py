"""
EPUB Conversion Script for Hello Algo Book

Installation Instructions:
1. Make sure you have Python 3.6+ installed
2. Install required dependencies:
   pip install pyyaml

3. Install Pandoc (required for EPUB conversion):
   Mac (using Homebrew):
   brew install pandoc

   Or download from: https://pandoc.org/installing.html

Usage:
- Place this script in the 'en/' folder
- Run: python convert-epub.py
- The output file 'hello_algo.epub' will be generated in the current directory

Author: 
Omar Olivares
https://olivares.cl
"""

import os
import sys
import subprocess
import yaml
import shutil

def load_config():
    with open("mkdocs.yml", "r") as f:
        return yaml.safe_load(f)


def extract_md_files(item, depth=0):
    if depth > 100:
        print("Warning: Infinite recursion detected", file=sys.stderr, flush=True)
        return []
    if isinstance(item, str):
        path = os.path.join("docs", item)
        if os.path.exists(path):
            return [item]
        print(f"Warning: Markdown file not found: {path}", file=sys.stderr, flush=True)
        return []
    files = []
    if isinstance(item, list):
        for sub in item:
            files += extract_md_files(sub, depth + 1)
    elif isinstance(item, dict):
        for value in item.values():
            files += extract_md_files(value, depth + 1)
    return files


def find_asset_dirs(root):
    asset_dirs = set()
    for dirpath, dirnames, _ in os.walk(root):
        for d in dirnames:
            if d.endswith(".assets"):
                full_path = os.path.join(dirpath, d).replace("\\", "/")
                rel_path = os.path.relpath(full_path, root).replace("\\", "/")
                asset_dirs.update(
                    {
                        full_path,
                        os.path.dirname(full_path).replace("\\", "/"),
                        rel_path,
                        os.path.join("docs", rel_path).replace("\\", "/"),
                    }
                )
    return list(asset_dirs)


def main():
    config = load_config()
    nav = config.get("nav", [])
    md_files = extract_md_files(nav)
    md_files_prefixed = [os.path.join("docs", md) for md in md_files if md]

    base_dirs = [".", "docs", "assets", "../assets"]
    asset_dirs = find_asset_dirs("docs")
    parent_assets = os.path.join("..", "assets")
    if os.path.exists(parent_assets):
        base_dirs.append(parent_assets)

    all_dirs = sorted(set(base_dirs + asset_dirs))
    resource_path = ":".join(all_dirs)

    cmd = [
        "pandoc",
        "-o",
        "hello_algo.epub",
        "--toc",
        "--toc-depth=2",
        "--metadata",
        "title=Hello Algo",
        "--resource-path",
        resource_path,
        "--mathjax",
        "--verbose",
        "--extract-media=extracted-media",
        "--wrap=none",
        "-t",
        "epub3",
        "--highlight-style=pygments",
        "-f",
        "markdown+fenced_code_blocks+fenced_code_attributes",
        "--epub-cover-image=./docs/assets/covers/chapter_hello_algo.jpg",
    ] + md_files_prefixed

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.getcwd(),
        )
    except subprocess.TimeoutExpired as e:
        print(f"Pandoc timed out: {e}", file=sys.stderr, flush=True)
        print(f"stdout: {e.stdout}", file=sys.stdout, flush=True)
        print(f"stderr: {e.stderr}", file=sys.stderr, flush=True)
        sys.exit(1)

    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr, flush=True)
    if result.returncode != 0:
        print(
            f"Pandoc failed with return code {result.returncode}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    media_dir = "extracted-media"
    if os.path.exists(media_dir):
        try:
            shutil.rmtree(media_dir)
            print(f"Cleaned up temporary files in {media_dir}", flush=True)
        except Exception as e:
            print(f"Error cleaning up {media_dir}: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
