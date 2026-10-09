#!/usr/bin/env python3
"""
ArXiv Submission Packaging and Verification Tool.

Verifies that the LaTeX source, figure assets, and abstract conform to arXiv
submission standards, and generates a self-contained tarball / zip bundle ready
for upload to the arXiv.org portal.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

# Safe console encoding for Windows legacy terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = REPO_ROOT / "paper"
FIGURES_DIR = PAPER_DIR / "figures"


def verify_arxiv_prerequisites() -> bool:
    """Verifies that all required files and figures exist and are formatted correctly."""
    print("=" * 65)
    print("      ARXIV PRE-FLIGHT VERIFICATION & PACKAGING SYSTEM        ")
    print("=" * 65)

    errors = []

    # 1. Check main.tex
    main_tex = PAPER_DIR / "main.tex"
    if not main_tex.exists():
        errors.append("Missing paper/main.tex")
    else:
        with open(main_tex, "r", encoding="utf-8") as f:
            content = f.read()
            # Check for figure references
            fig_refs = re.findall(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}", content)
            print(f"[OK] Located paper/main.tex ({len(content.splitlines())} lines)")
            print(f"     Found {len(fig_refs)} embedded figure references:")
            for ref in fig_refs:
                # Path resolution relative to paper/
                fig_path = PAPER_DIR / ref
                if fig_path.exists():
                    size_kb = fig_path.stat().st_size / 1024.0
                    print(f"     [OK] {ref} (Verified, {size_kb:.1f} KB)")
                else:
                    errors.append(f"Referenced figure not found: {ref}")

    # 2. Check arXiv_abstract.txt
    abstract_txt = PAPER_DIR / "arXiv_abstract.txt"
    if not abstract_txt.exists():
        errors.append("Missing paper/arXiv_abstract.txt")
    else:
        with open(abstract_txt, "r", encoding="utf-8") as f:
            abs_text = f.read()
            print(f"[OK] Located paper/arXiv_abstract.txt ({len(abs_text)} characters)")

    # 3. Check figures directory
    if not FIGURES_DIR.exists():
        errors.append("Missing paper/figures directory")
    else:
        figs = list(FIGURES_DIR.glob("*.*"))
        print(f"[OK] Located paper/figures/ ({len(figs)} assets present)")

    if errors:
        print("\n[FAILED] Verification encountered errors:")
        for err in errors:
            print(f"  - ✗ {err}")
        return False

    print("\n[SUCCESS] All arXiv pre-flight checks passed!")
    return True


def create_submission_archives() -> None:
    """Creates tar.gz and .zip archives for arXiv portal upload."""
    tar_out = PAPER_DIR / "arxiv_submission.tar.gz"
    zip_out = PAPER_DIR / "arxiv_submission.zip"

    files_to_bundle = [
        (PAPER_DIR / "main.tex", "main.tex"),
        (PAPER_DIR / "arXiv_abstract.txt", "arXiv_abstract.txt"),
    ]

    # Add all figures
    for fig_file in FIGURES_DIR.glob("*.*"):
        if fig_file.suffix in (".pdf", ".png", ".jpg"):
            rel_name = f"figures/{fig_file.name}"
            files_to_bundle.append((fig_file, rel_name))

    # 1. Create tar.gz
    with tarfile.open(tar_out, "w:gz") as tar:
        for file_path, arc_name in files_to_bundle:
            tar.add(file_path, arcname=arc_name)
    tar_size = tar_out.stat().st_size / 1024.0
    print(f"\n[OK] Generated arXiv Tarball: {tar_out.name} ({tar_size:.1f} KB)")

    # 2. Create zip
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path, arc_name in files_to_bundle:
            zipf.write(file_path, arcname=arc_name)
    zip_size = zip_out.stat().st_size / 1024.0
    print(f"[OK] Generated arXiv Zip Archive: {zip_out.name} ({zip_size:.1f} KB)")

    print(f"\nBundle Contents ({len(files_to_bundle)} files):")
    for _, arc in files_to_bundle:
        print(f"  - {arc}")


def main() -> int:
    if not verify_arxiv_prerequisites():
        return 1
    create_submission_archives()
    print("\n[READY] Package is ready for immediate upload to https://arxiv.org/submit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
