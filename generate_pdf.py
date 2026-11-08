"""
PDF Generator for Solution Doc using Headless Edge Browser.
Compiles solution_doc.html into a pixel-perfect 2-page PDF and verifies page count.
"""

import os
import subprocess
import re
import sys


def generate_pdf():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)
    if not edge_exe:
        print("Microsoft Edge not found.")
        sys.exit(1)

    html_path = os.path.abspath("solution_doc.html")
    pdf_path = os.path.abspath("solution_doc.pdf")
    file_uri = "file:///" + html_path.replace("\\", "/")

    cmd = [
        edge_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        file_uri
    ]

    print(f"Compiling {html_path} -> {pdf_path}...")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        with open(pdf_path, "rb") as f:
            content = f.read()
            pages = len(re.findall(rb"/Type\s*/Page\b", content))
        print(f"✅ Generated {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")
        print(f"📄 Exact Page Count: {pages} pages")
        if pages == 2:
            print("🎯 PERFECT: The PDF is strictly 2 pages!")
        else:
            print(f"⚠️ Warning: Expected 2 pages, got {pages}")
    else:
        print(f"❌ Failed to generate PDF. Exit code: {res.returncode}")
        print("Stderr:", res.stderr)


if __name__ == "__main__":
    generate_pdf()
