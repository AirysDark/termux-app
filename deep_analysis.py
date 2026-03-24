import os
import re
import json

# -----------------------------
# CONFIG
# -----------------------------
PORT_DIR = os.path.abspath(".")          # Run inside the port folder
OUTPUT_JSON = os.path.join(PORT_DIR, "deep_analysis.json")

# File extensions to analyze
ANALYZE_EXTENSIONS = [".java", ".js", ".ts"]

# Regex patterns
FUNCTION_PATTERNS = {
    ".java": r"\b(?:public|private|protected)?\s*(?:static\s+)?(?:[\w<>[\]]+\s+)+(\w+)\s*\(",
    ".js": r"function\s+(\w+)\s*\(",
    ".ts": r"function\s+(\w+)\s*\("
}

IMPORT_PATTERNS = {
    ".java": r"import\s+([\w\.]+);",
    ".js": r"import\s+(?:.*\s+from\s+)?['\"]([^'\"]+)['\"]",
    ".ts": r"import\s+(?:.*\s+from\s+)?['\"]([^'\"]+)['\"]"
}

COMMENT_PATTERNS = {
    ".java": r"(/\*\*.*?\*/|//.*?$)",
    ".js": r"(//.*?$|/\*.*?\*/)",
    ".ts": r"(//.*?$|/\*.*?\*/)"
}

# -----------------------------
# FUNCTIONS
# -----------------------------
def scan_files(port_dir):
    all_files = []
    for root, dirs, files in os.walk(port_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, port_dir)
            ext = os.path.splitext(f)[1].lower()
            if ext in ANALYZE_EXTENSIONS:
                all_files.append({"path": rel_path, "ext": ext, "full": full_path})
    return all_files

def extract_functions(file):
    ext = file["ext"]
    pattern = FUNCTION_PATTERNS[ext]
    try:
        with open(file["full"], encoding="utf-8") as f:
            content = f.read()
        return re.findall(pattern, content, re.MULTILINE | re.DOTALL)
    except Exception as e:
        return [f"ERROR reading file: {e}"]

def extract_imports(file):
    ext = file["ext"]
    pattern = IMPORT_PATTERNS[ext]
    try:
        with open(file["full"], encoding="utf-8") as f:
            content = f.read()
        return re.findall(pattern, content, re.MULTILINE)
    except Exception as e:
        return [f"ERROR reading imports: {e}"]

def extract_comments(file):
    ext = file["ext"]
    pattern = COMMENT_PATTERNS[ext]
    try:
        with open(file["full"], encoding="utf-8") as f:
            content = f.read()
        return re.findall(pattern, content, re.MULTILINE | re.DOTALL)
    except Exception as e:
        return [f"ERROR reading comments: {e}"]

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("🔎 Scanning port folder for code files...")
    files = scan_files(PORT_DIR)
    print(f"📄 Found {len(files)} files for analysis.")

    analysis = {}
    for file in files:
        analysis[file["path"]] = {
            "functions": extract_functions(file),
            "imports": extract_imports(file),
            "comments": extract_comments(file)
        }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print(f"✅ Deep analysis complete. Output saved to {OUTPUT_JSON}")
    print("💡 You can now use this JSON to map Termux functions, dependencies, and comments for Linux rebuild.")

if __name__ == "__main__":
    main()
