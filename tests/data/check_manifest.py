#!/usr/bin/env python3
"""check_manifest.py - are the litmus files the ones MANIFEST.tsv names, and do they hold what the truth tables say?

Standard library only, no network: every file of the manifest is there with its size and md5 (the file's, and its
content's once unzipped), holds as many records as written, each pair of read files holds the same names in the same
order, every molecule of truth.tsv is in its child's read files, and the set's premise holds in the summary - no read
end of a parent passes the rule for the child's bacterium.

  python3 tests/data/check_manifest.py        # exit 0, or 1 with a line for each thing that is wrong
"""
import csv
import gzip
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def md5(path, unzip=False):
    h = hashlib.md5()
    with (gzip.open(path, "rb") if unzip else open(path, "rb")) as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def table(rel):
    with open(os.path.join(HERE, rel), newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def names(path):
    with gzip.open(path, "rt") as fh:
        return [line[1:].rstrip("\n") for i, line in enumerate(fh) if i % 4 == 0]


def records(path):
    if path.endswith(".fq.gz"):
        return len(names(path))
    if path.endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            return sum(1 for line in fh if line.startswith(">"))
    with open(path) as fh:
        return sum(1 for _ in fh) - 1


def problems():
    out = []
    manifest = table("MANIFEST.tsv")
    if not manifest:
        return ["MANIFEST.tsv is empty"]
    for row in manifest:
        p = os.path.join(HERE, row["path"])
        if not os.path.isfile(p):
            out.append("%s: not there" % row["path"])
            continue
        zipped = p.endswith(".gz")
        if os.path.getsize(p) != int(row["bytes"]):
            out.append("%s: %d bytes, the manifest says %s" % (row["path"], os.path.getsize(p), row["bytes"]))
        if md5(p) != row["md5"]:
            out.append("%s: md5 differs from the manifest's" % row["path"])
        if md5(p, unzip=zipped) != row["content_md5"]:
            out.append("%s: the content's md5 differs from the manifest's" % row["path"])
        if records(p) != int(row["records"]):
            out.append("%s: %d records, the manifest says %s" % (row["path"], records(p), row["records"]))
    listed = set(r["path"] for r in manifest)
    for r1 in sorted(x for x in listed if x.endswith(".r1.fq.gz")):
        r2 = r1[:-len(".r1.fq.gz")] + ".r2.fq.gz"
        if r2 not in listed:
            out.append("%s: no second end in the manifest" % r1)
            continue
        a, b = names(os.path.join(HERE, r1)), names(os.path.join(HERE, r2))
        if a != b:
            out.append("%s and its second end do not hold the same names in the same order" % r1)
        if a != sorted(a) or len(set(a)) != len(a):
            out.append("%s: names not sorted, or one twice" % r1)
    truth = table("litmus/truth.tsv")
    by_locus = {}
    for row in truth:
        by_locus.setdefault((row["trio"], row["locus"]), []).append(row["molecule"])
    for (trio, locus), molecules in sorted(by_locus.items()):
        have = set(names(os.path.join(HERE, "litmus", trio, locus, "child.r1.fq.gz")))
        gone = [m for m in molecules if m not in have]
        if gone:
            out.append("truth.tsv %s %s: %d molecules not in the child's reads" % (trio, locus, len(gone)))
    summary = table("litmus/truth_summary.tsv")
    for row in summary:
        if row["role"] != "child" and int(row["ends_passing"]) != 0:
            out.append("truth_summary.tsv %s %s: %s read ends of the %s pass the rule for the child's bacterium"
                       % (row["trio"], row["locus"], row["ends_passing"], row["role"]))
    for trio in sorted(set(r["trio"] for r in summary)):
        if not any(int(r["ends_passing"]) for r in summary if r["trio"] == trio and r["role"] == "child"):
            out.append("truth_summary.tsv %s: not one read end of the child passes the rule" % trio)
    return out


def main():
    found = problems()
    for line in found:
        print(line)
    print("litmus set: %s" % ("ok" if not found else "%d problem%s" % (len(found), "" if len(found) == 1 else "s")))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
