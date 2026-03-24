name: Analyze & Package Termux Port

on:
  workflow_dispatch:
  push:
    branches:
      - master
      - "termux-port/**"

jobs:
  validate-analyze-package:
    runs-on: ubuntu-latest

    steps:
      # 1️⃣ Checkout repository
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 1

      # 2️⃣ Setup Python
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # 3️⃣ Prepare output folder
      - name: Create analysis output folder
        run: mkdir -p analysis_output

      # 4️⃣ Validate port, scan functions, XML, and extra keys
      - name: Validate port and analyze files
        run: |
          python3 <<'EOF'
          import os, re, json, shutil, sys, zipfile

          PORT_DIR = os.path.join(os.getcwd(), "extracted-termux")
          OUTPUT_JSON = os.path.join("analysis_output", "analysis.json")
          OUTPUT_TXT = os.path.join("analysis_output", "summary.txt")
          ZIP_OUTPUT_DIR = os.path.join("analysis_output", "zips")
          os.makedirs(ZIP_OUTPUT_DIR, exist_ok=True)

          REQUIRED_TOP_FOLDERS = ["terminal", "app", "view"]
          EXTRA_FOLDERS = [os.path.join("app","com","termux","app","fragments","settings"),
                           os.path.join("terminal","io")]

          FUNCTION_EXTS = [".java", ".js", ".ts"]
          FUNCTION_PATTERNS = {
              ".java": r"\b(?:public|private|protected)?\s*(?:static\s+)?(?:[\w<>[\]]+\s+)+(\w+)\s*\(",
              ".js": r"function\s+(\w+)\s*\(",
              ".ts": r"function\s+(\w+)\s*\("
          }

          # ---- Validation ----
          missing_top = [f for f in REQUIRED_TOP_FOLDERS if not os.path.exists(os.path.join(PORT_DIR,f))]
          missing_extra = [f for f in EXTRA_FOLDERS if not os.path.exists(os.path.join(PORT_DIR,f))]

          if missing_top or missing_extra:
              print("🚨 Missing required folders/files:")
              if missing_top: print("   - Top-level:", missing_top)
              if missing_extra: print("   - Extra:", missing_extra)
              sys.exit(1)

          # ---- Scan all files and extensions ----
          all_files = []
          extensions = set()
          for root, dirs, files in os.walk(PORT_DIR):
              for f in files:
                  rel_path = os.path.relpath(os.path.join(root,f), PORT_DIR)
                  ext = os.path.splitext(f)[1].lower()
                  extensions.add(ext)
                  all_files.append(rel_path)

          # ---- Scan functions ----
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

          # ---- XML layouts and extra keys ----
          xml_files = [f for f in all_files if f.endswith(".xml")]
          extra_keys_files = [f for f in all_files if "extra" in f.lower()]

          # ---- Save reports ----
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

          # ---- Split into module zip files ----
          def zip_folder(src_folder, zip_name):
              zip_path = os.path.join(ZIP_OUTPUT_DIR, zip_name)
              with zipfile.ZipFile(zip_path,'w', zipfile.ZIP_DEFLATED) as zf:
                  for root, dirs, files in os.walk(src_folder):
                      for f in files:
                          full_path = os.path.join(root,f)
                          rel_path = os.path.relpath(full_path, src_folder)
                          zf.write(full_path, rel_path)
              print(f"✅ Created zip: {zip_path}")

          zip_folder(os.path.join(PORT_DIR,"terminal"), "terminal-engine.zip")
          zip_folder(os.path.join(PORT_DIR,"terminal-view"), "terminal-render.zip")
          zip_folder(os.path.join(PORT_DIR,"app"), "ui-app.zip")
          zip_folder(os.path.join(PORT_DIR,"shared"), "shared.zip")
          zip_folder(PORT_DIR, "full-port.zip")
          EOF

      # 5️⃣ Upload all artifacts
      - name: Upload analysis & module zips
        uses: actions/upload-artifact@v6
        with:
          name: termux-analysis-and-modules
          path: analysis_output
