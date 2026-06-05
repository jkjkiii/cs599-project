"""Build PDF from markdown with bookmarks using pandoc + xelatex."""
import re
import subprocess
import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Step 1: Generate .tex from markdown
print("Step 1: Converting MD to TeX via pandoc...")
result = subprocess.run([
    "pandoc", "docs/CS599_大作业报告.md",
    "-o", "docs/report.tex",
    "--standalone",
    "--toc", "--toc-depth=3",
    "-N",
], capture_output=True)
if result.returncode != 0:
    print("Pandoc stderr:", result.stderr.decode("utf-8", errors="replace"))
    raise RuntimeError("Pandoc failed")
print("Done.")

# Step 2: Read and fix the .tex file
print("Step 2: Fixing TeX file for Chinese support...")
with open("docs/report.tex", "r", encoding="utf-8") as f:
    tex = f.read()

# Normalize line endings to LF
tex = tex.replace("\r\n", "\n").replace("\r", "\n")

# Fix 1: Replace \linethickness everywhere (only valid in picture env)
tex = tex.replace("\\linethickness", "0.4pt")

# Fix 2: Replace documentclass for Chinese support
tex = tex.replace(
    "\\documentclass[]{article}",
    "\\documentclass[a4paper,12pt]{ctexart}"
)

# Fix 3: Remove fixltx2e (obsolete, causes error with ctex)
tex = tex.replace(
    "\\usepackage{fixltx2e} % provides \\textsubscript\n", ""
)

# Fix 4: Remove lmodern (redundant with ctex)
tex = tex.replace("\\usepackage{lmodern}\n", "")

# Fix 5: Remove ifxetex/ifluatex package (ctex loads fontspec internally)
tex = tex.replace("\\usepackage{ifxetex,ifluatex}\n", "")

# Fix 6: Remove the entire ifnum block that loads fontspec/mathspec
tex = re.sub(
    r'\\ifnum 0\\ifxetex 1\\fi\\ifluatex 1\\fi=0 % if pdftex\n'
    r'  \\usepackage\[T1\]\{fontenc\}\n'
    r'  \\usepackage\[utf8\]\{inputenc\}\n'
    r'\\else % if luatex or xelatex\n'
    r'  \\ifxetex\n'
    r'    \\usepackage\{mathspec\}\n'
    r'  \\else\n'
    r'    \\usepackage\{fontspec\}\n'
    r'  \\fi\n'
    r'  \\defaultfontfeatures\{Ligatures=TeX,Scale=MatchLowercase\}\n'
    r'\\fi\n',
    '',
    tex
)

# Fix 7: Ensure hyperref has bookmarks enabled
tex = tex.replace(
    "\\usepackage[unicode=true]{hyperref}",
    "\\usepackage[unicode=true,bookmarks=true,bookmarksnumbered=true,"
    "bookmarksopen=true,bookmarksopenlevel=2]{hyperref}"
)

# Fix 8: Add CJK font setup and geometry before begin{document}
preamble_additions = (
    "\n"
    "% Page geometry\n"
    "\\usepackage[top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry}\n"
    "\n"
    "% Chinese font setup\n"
    "\\setCJKmainfont{SimSun}\n"
    "\\setCJKsansfont{SimHei}\n"
    "\\setCJKmonofont{KaiTi}\n"
    "\\setmonofont{Consolas}\n"
    "\n"
    "% Fix horizontal rule\n"
    "\\newcommand{\\myhrule}{\\par\\noindent\\rule{\\linewidth}{0.4pt}\\par}\n"
    "\n"
)
tex = tex.replace("\\begin{document}", preamble_additions + "\\begin{document}")

# Fix 9: Replace broken \rule centers with proper horizontal rules
tex = tex.replace(
    "\\begin{center}\\rule{0.5\\linewidth}{0.4pt}\\end{center}",
    "\\myhrule"
)

print("Done.")

# Write fixed tex
with open("docs/report.tex", "w", encoding="utf-8", newline="\n") as f:
    f.write(tex)

# Step 3: Compile with xelatex (two passes for TOC)
for i in range(2):
    print(f"Step 3.{i+1}: xelatex pass {i+1}...")
    result = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-output-directory=docs",
         "docs/report.tex"],
        capture_output=True
    )
    if result.returncode != 0:
        log_file = "docs/report.log"
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            for line in log_content.split("\n"):
                if line.startswith("!") or "Error" in line:
                    print(line)
        print("\nxelatex failed. Check docs/report.log for details.")
        sys.exit(1)

print("PDF generated: docs/report.pdf")

# Copy to final name
import shutil
shutil.copy("docs/report.pdf", "docs/CS599_大作业报告.pdf")
print("Copied to: docs/CS599_大作业报告.pdf")

# Clean up aux files
for ext in [".aux", ".log", ".out", ".toc"]:
    fpath = f"docs/report{ext}"
    if os.path.exists(fpath):
        os.remove(fpath)
print("Cleaned up auxiliary files.")
print("\nDone! PDF with bookmarks is ready at: docs/CS599_大作业报告.pdf")
