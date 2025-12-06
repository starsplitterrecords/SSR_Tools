#!/usr/bin/env python3

import os
from datetime import datetime

CODE_EXT = {
    ".py", ".js", ".ts", ".tsx", ".json", ".yml", ".yaml",
    ".md", ".txt", ".html", ".css", ".ini"
}

IGNORE_DIRS = {
    "__pycache__", "_pycache__", ".git", ".idea", ".vscode",
    "venv", "venv311", ".venv",
    "code_dumps",
}

def walk_tree(root: str):
    lines = []

    for dirpath, dirnames, files in os.walk(root):
        # prune ignores
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        rel = os.path.relpath(dirpath, root)
        prefix = "" if rel == "." else rel

        lines.append(prefix + "/")

        for f in files:
            lines.append(os.path.join(prefix, f) if prefix else f)

    return "\n".join(lines)

def collect_files(root: str):
    out = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in CODE_EXT:
                out.append(os.path.join(dirpath, f))
    return sorted(out)

def concat(files, out_path, tree_text):
    with open(out_path, "w", encoding="utf-8") as w:
        w.write("# === REPO TREE ===\n")
        w.write(tree_text)
        w.write("\n\n# === FILE CONTENTS ===\n")

        for path in files:
            w.write(f"\n\n# >>> {path}\n\n")
            with open(path, "r", encoding="utf-8", errors="replace") as r:
                w.write(r.read())

if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.join(repo_root, "dumps"), exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_file = os.path.join(repo_root, "code_dumps", f"repo_dump_{stamp}.txt")

    tree_text = walk_tree(repo_root)
    files = collect_files(repo_root)

    concat(files, out_file, tree_text)
