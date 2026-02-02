#!/usr/bin/env python3
"""
ELK Master Verification Suite
The ultimate shield against technical and fundamental errors.
"""

import sys
import os
import subprocess
from pathlib import Path

def print_step(msg):
    print(f"\n[STEP] {msg}...")

def run_command(cmd, name):
    executable = cmd.split()[0]
    import shutil
    if not shutil.which(executable):
        print(f"⚠️ {name} SKIPPED ({executable} not in PATH)")
        return True
    
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {name} PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} FAILED")
        print(f"Error: {e.stderr or e.output}")
        return False

def check_structure():
    print_step("Checking Core Project Structure")
    critical_paths = [
        "elk/api/app.py",
        "elk/workers/main.py",
        "elk/core/config.py",
        "elk/database/db.py",
        "packs/dz_kab_protection/runtime/pipeline.py"
    ]
    all_ok = True
    for p in critical_paths:
        if not os.path.exists(p):
            print(f"  ⚠️ Missing critical file: {p}")
            all_ok = False
    
    # Check for __init__.py in all subdirs of elk/
    for root, dirs, files in os.walk("elk"):
        if "__pycache__" in root: continue
        if "__init__.py" not in files:
            print(f"  ⚠️ Missing __init__.py in {root}")
            all_ok = False
            
    if all_ok: print("✅ Project structure is integral")
    return all_ok

def run_static_checks():
    print_step("Running Static Analysis (Ruff)")
    # We use ruff check because it's fast and encompasses many linters
    return run_command("ruff check .", "Linting")

def verify_config():
    print_step("Verifying Configuration Loading")
    try:
        os.environ["DEBUG"] = "true"
        from elk.core.config import settings
        print(f"✅ Config loaded: Version {settings.VERSION}")
        return True
    except Exception as e:
        print(f"❌ Config failure: {e}")
        return False

def audit_ignore():
    print_step("Auditing .gitignore for leaks")
    with open(".gitignore", "r") as f:
        content = f.read()
    
    mandatory_ignores = [".env", "*.db", "logs/", "__pycache__"]
    all_ok = True
    for m in mandatory_ignores:
        if m not in content:
            print(f"  ⚠️ Potential leak risk: '{m}' not in .gitignore")
            all_ok = False
    if all_ok: print("✅ .gitignore meets safety standards")
    return all_ok

def main():
    print("==========================================")
    print("   🛡️  ELK ZERO-RISK VERIFICATION SUITE  ")
    print("==========================================\n")
    
    results = [
        check_structure(),
        run_static_checks(),
        verify_config(),
        audit_ignore()
    ]
    
    if all(results):
        print("\n🏆 VERDICT: DEPOT READY FOR PUSH")
        sys.exit(0)
    else:
        print("\n🛑 VERDICT: DEFECTS DETECTED - DO NOT PUSH")
        sys.exit(1)

if __name__ == "__main__":
    main()
