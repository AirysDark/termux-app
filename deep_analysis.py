import os, re, json, shutil

PORT_DIR = "/path/to/your/termux-port"  # Point this to your local folder
BUILD_DIR = os.path.join(PORT_DIR, "extracted_termux")
OUTPUT_JSON = os.path.join(BUILD_DIR, "scan_report.json")
OUTPUT_TXT = os.path.join(BUILD_DIR, "scan_summary.txt")

REQUIRED_TOP_FOLDERS = ["terminal", "app", "view"]
EXTRA_FOLDERS = ["app/com/termux/app/fragments/settings", "terminal/io"]
FUNCTION_EXTS = [".java", ".js", ".ts"]
FUNCTION_PATTERNS = {
    ".java": r"\b(?:public|private|protected)?\s*(?:static\s+)?(?:[\w<>[\]]+\s+)+(\w+)\s*\(",
    ".js": r"function\s+(\w+)\s*\(",
    ".ts": r"function\s+(\w+)\s*\("
}

# Create extraction folder
os.makedirs(BUILD_DIR, exist_ok=True)

# -----------------------------
# Verify folders
# -----------------------------
missing_top = [f for f in REQUIRED_TOP_FOLDERS if not os.path.exists(os.path.join(PORT_DIR,f))]
missing_extra = [f for f in EXTRA_FOLDERS if not os.path.exists(os.path.join(PORT_DIR,f))]

if missing_top or missing_extra:
    print("🚨 Missing required folders/files in port:")
    if missing_top: print("   - Top-level:", missing_top)
    if missing_extra: print("   - Extra:", missing_extra)
    # Do not exit — you can continue scanning local files that exist

# -----------------------------
# Scan files and extensions
# -----------------------------
all_files = []
extensions = set()
for root, dirs, files in os.walk(PORT_DIR):
    for f in files:
        rel_path = os.path.relpath(os.path.join(root,f), PORT_DIR)
        ext = os.path.splitext(f)[1].lower()
        extensions.add(ext)
        all_files.append(rel_path)

# -----------------------------
# Scan functions/methods
# -----------------------------
functions = {}
for file in all_files:
    ext = os.path.splitext(file)[1].lower()
    if ext in FUNCTION_EXTS:
        pattern = FUNCTION_PATTERNS.get(ext)
        try:
            with open(os.path.join(PORT_DIR,file), encoding="utf-8") as f:
                content = f.read()
            matches = re.findall(pattern, content)
            if matches:
                functions[file] = matches
        except Exception as e:
            functions[file] = [f"ERROR reading file: {e}"]

# -----------------------------
# Detect XML layouts and extra keys
# -----------------------------
xml_files = [f for f in all_files if f.endswith(".xml")]
extra_keys_files = [f for f in all_files if "extra" in f.lower()]

# -----------------------------
# Save reports
# -----------------------------
report = {
    "missing_top_level": missing_top,
    "missing_extra_folders": missing_extra,
    "total_files": len(all_files),
    "extensions": sorted(list(extensions)),
    "all_files": all_files,
    "functions": functions,
    "xml_files": xml_files,
    "extra_keys_files": extra_keys_files
}

with open(OUTPUT_JSON,"w",encoding="utf-8") as f:
    json.dump(report, f, indent=2)

with open(OUTPUT_TXT,"w",encoding="utf-8") as f:
    f.write(f"🚀 Termux Port Scan Summary\n")
    f.write(f"Total files scanned: {len(all_files)}\n")
    f.write(f"Extensions found: {sorted(list(extensions))}\n\n")
    f.write("🔹 Functions detected:\n")
    for file, funcs in functions.items():
        f.write(f"  {file} -> {len(funcs)} functions: {funcs}\n")
    f.write("\n🔹 XML layout files:\n")
    for xf in xml_files:
        f.write(f"  {xf}\n")
    f.write("\n🔹 Extra keys files:\n")
    for ek in extra_keys_files:
        f.write(f"  {ek}\n")

print(f"✅ Scan complete. Reports saved to {OUTPUT_JSON} and {OUTPUT_TXT}")