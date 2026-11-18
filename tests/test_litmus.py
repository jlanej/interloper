"""The litmus set (tests/data/, docs/validation.md): real reads of two contaminated 1000 Genomes libraries.

Two checks. The files are the ones the manifest names. And - where minimap2 is installed - the rule the whole method
rests on, run again on those reads: an end is the bacterium's when it aligns to the named genome over >= 90% of its
length at >= 98% identity. It must find the child's molecules that truth.tsv lists, and not one read end of a parent.
"""
import csv
import importlib.util
import os
import shutil
import subprocess

import pytest

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DATA, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(rel):
    with open(os.path.join(DATA, rel), newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def test_the_files_are_the_manifests():
    assert load("check_manifest").problems() == []


def test_what_the_set_holds():
    summary = rows("litmus/truth_summary.tsv")
    child = lambda trio: [r for r in summary if r["trio"] == trio and r["role"] == "child"]
    parents = [r for r in summary if r["role"] != "child"]
    # each child's library holds the bacterium at its places; no parent's does, at any of them
    assert sum(int(r["ends_passing"]) for r in child("HG01376")) >= 80
    assert sum(int(r["ends_passing"]) for r in child("NA18521")) >= 80
    assert parents and all(int(r["ends_passing"]) == 0 for r in parents)
    assert sum(int(r["read_ends"]) for r in parents) > 10000
    # the place whose reads are bacterial by label and are NOT the named genome: a flag without a name
    unnamed = [r for r in child("HG01376") if r["locus"] == "chrX_unnamed"]
    assert len(unnamed) == 1 and int(unnamed[0]["ends_passing"]) == 0


@pytest.mark.skipif(shutil.which("minimap2") is None, reason="minimap2 is not installed")
def test_the_rule_finds_the_same_molecules_again():
    make = load("make_litmus")
    truth, summary = make.derive_truth()
    t = dict((k, i) for i, k in enumerate(make.TRUTH_HEADER))
    s = dict((k, i) for i, k in enumerate(make.SUMMARY_HEADER))
    listed, listed_summary = rows("litmus/truth.tsv"), rows("litmus/truth_summary.tsv")
    # whatever the minimap2: the same molecules of each child are the bacterium's, and no read end of a parent is
    assert sorted((r[t["trio"]], r[t["locus"]], r[t["molecule"]]) for r in truth if r[t["ends_passing"]]) == \
        sorted((r["trio"], r["locus"], r["molecule"]) for r in listed if int(r["ends_passing"]))
    assert all(r[s["ends_passing"]] == 0 for r in summary if r[s["role"]] != "child")
    # with the minimap2 the tables were derived with: every count the same. Four read ends sit exactly on the identity
    # rule (3 mismatches in 150 bases) and two near the aligned one, so another release may move those by an end
    version = subprocess.run(["minimap2", "--version"], stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
    if version != make.TRUTH_MINIMAP2:
        pytest.skip("minimap2 %s: the molecules agree; the per-end counts are compared with %s alone" % (version, make.TRUTH_MINIMAP2))
    assert sorted((r[t["trio"]], r[t["locus"]], r[t["molecule"]], str(r[t["ends_passing"]])) for r in truth) == \
        sorted((r["trio"], r["locus"], r["molecule"], r["ends_passing"]) for r in listed)
    keys = ("trio", "locus", "role", "pairs", "read_ends", "ends_passing", "molecules_both_ends_passing")
    assert [[str(r[s[k]]) for k in keys] for r in summary] == [[r[k] for k in keys] for r in listed_summary]
