"""`interloper doctor`: are the tools the method needs here, and which versions?

The method shells out to three programs and builds on one Python package (docs/design.md):

  kraken2          the k-mer screen (through nonhuman-screen)
  minimap2         the alignment that verifies a screen's label
  samtools         reading BAM/CRAM
  nonhuman-screen  the kraken2 runner and the non-human partition (optional at import time: `pip install interloper[screen]`)

The container image holds all four; this command is how the image, and any other install, says so.
"""
import importlib.metadata
import json
import shutil
import subprocess

# name, the arguments that make it print its version, required
PROGRAMS = (
    ("kraken2", ["--version"], True),
    ("minimap2", ["--version"], True),
    ("samtools", ["--version"], True),
)
PACKAGES = (("nonhuman-screen", True),)


def first_line(text):
    """The first non-empty line of a program's version output."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def program_version(name, args, timeout=20):
    """(path, version line) of a program on PATH; (None, "") when it is not there, (path, "") when it would not say."""
    path = shutil.which(name)
    if path is None:
        return None, ""
    try:
        done = subprocess.run([path] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return path, ""
    # bytes, read leniently: a program's version text is not always UTF-8 (a build's flags, an author's name)
    return path, first_line(done.stdout.decode("utf-8", errors="replace"))


def package_version(name):
    """The installed version of a Python distribution, or None."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def check():
    """One row per tool: name, kind, required, found, version, where."""
    rows = []
    for name, args, required in PROGRAMS:
        path, version = program_version(name, args)
        rows.append({"name": name, "kind": "program", "required": required, "found": path is not None,
                     "version": version, "where": path or ""})
    for name, required in PACKAGES:
        version = package_version(name)
        rows.append({"name": name, "kind": "python package", "required": required, "found": version is not None,
                     "version": version or "", "where": ""})
    return rows


def run(as_json=False, out=None):
    """Print the check; return 0 when every required tool is found, 1 otherwise."""
    import sys
    out = out or sys.stdout
    rows = check()
    missing = [r["name"] for r in rows if r["required"] and not r["found"]]
    if as_json:
        json.dump({"ok": not missing, "missing": missing, "tools": rows}, out, indent=2)
        out.write("\n")
    else:
        width = max(len(r["name"]) for r in rows)
        for r in rows:
            state = (r["version"] or "found, version not reported") if r["found"] else "MISSING"
            out.write("%-*s  %s%s\n" % (width, r["name"], state, ("  (%s)" % r["where"]) if r["where"] else ""))
        out.write("ok\n" if not missing else "missing: %s\n" % ", ".join(missing))
    return 0 if not missing else 1
