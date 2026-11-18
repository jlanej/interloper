"""The data rule (CONTRIBUTING.md), as far as a machine can check it.

Only publicly available data may appear in this repository. These tests catch the mechanical ways that rule breaks:
a path from someone's machine in a file, sequencing data outside the manifested test set, a test data file without a
manifest row, a manifest row without a public source. They cannot tell whether a number in a document came from
public data: that stays with the author and the reviewer.
"""
import csv
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".pytest_cache", ".venv", "venv", "work", "ci_out"}
# a path on somebody's machine or cluster: a home, a mounted volume, a scratch area
LOCAL_PATH = re.compile(r"(?<![\w.:/-])/(?:Users|home|Volumes|scratch|private/tmp|mnt|projects|panfs)/[\w.-]+")
SEQUENCING_DATA = (".bam", ".bai", ".cram", ".crai", ".vcf", ".vcf.gz", ".bcf", ".fq", ".fq.gz", ".fastq", ".fastq.gz",
                   ".fa", ".fa.gz", ".fna", ".fna.gz", ".fasta", ".fasta.gz", ".k2d")
# where test data may come from: the 1000 Genomes public mirror, NCBI, the public reference by its file name
PUBLIC_SOURCES = ("https://1000genomes.s3.amazonaws.com/", "https://api.ncbi.nlm.nih.gov/",
                  "GRCh38_full_analysis_set_plus_decoy_hla.fa")


def tracked_files():
    """The repository's files, relative to its root: git's list in a checkout, else a walk."""
    try:
        done = subprocess.run(["git", "-C", ROOT, "ls-files"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              universal_newlines=True)
        listed = [f for f in done.stdout.splitlines() if f]
        if done.returncode == 0 and listed:
            # files written but not yet added are checked too: the rule is about what could be committed
            more = subprocess.run(["git", "-C", ROOT, "ls-files", "--others", "--exclude-standard"],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
            return sorted(set(listed) | set(f for f in more.stdout.splitlines() if f))
    except OSError:
        pass
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        found += [os.path.relpath(os.path.join(base, f), ROOT) for f in files]
    return sorted(found)


def text_of(rel):
    """A file's text, or None when it is not text (the gzipped test data)."""
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return None


def test_no_path_from_a_private_machine():
    hits = []
    for rel in tracked_files():
        if rel == os.path.join("tests", "test_public_only.py"):
            continue                                     # this file names the patterns it looks for
        text = text_of(rel)
        for n, line in enumerate((text or "").splitlines(), 1):
            if LOCAL_PATH.search(line):
                hits.append("%s:%d: %s" % (rel, n, line.strip()[:100]))
    assert hits == []


def test_sequencing_data_lives_in_the_manifested_test_set_alone():
    outside = [rel for rel in tracked_files()
               if rel.lower().endswith(SEQUENCING_DATA) and not rel.replace(os.sep, "/").startswith("tests/data/")]
    assert outside == []


def test_every_test_data_file_has_a_manifest_row_with_a_public_source():
    with open(os.path.join(ROOT, "tests", "data", "MANIFEST.tsv"), newline="") as fh:
        manifest = dict((r["path"], r) for r in csv.DictReader(fh, delimiter="\t"))
    data = [rel.replace(os.sep, "/")[len("tests/data/"):] for rel in tracked_files()
            if rel.replace(os.sep, "/").startswith("tests/data/")]
    unlisted = [f for f in data if f not in manifest and not f.endswith(".py") and f != "MANIFEST.tsv"]
    assert unlisted == []
    for path, row in manifest.items():
        derived = row["source"] == "." and row["made_by"].startswith("make_litmus.py")
        assert derived or row["source"].startswith(PUBLIC_SOURCES), "%s: source %r is not a public one" % (path, row["source"])
