#!/usr/bin/env python3
"""make_litmus.py - the litmus reads: two contaminated 1000 Genomes libraries, rebuilt from public files.

Two children of the 1000 Genomes high-coverage trios carry a bacterium's DNA in their sequencing library and not in
their parents' (docs/validation.md): HG01376 (Methylobacterium organophilum) and NA18521 (Staphylococcus epidermidis).
A few of each bacterium's reads have a short exact match to a human gene, are placed there by the aligner with the
rest clipped and the mate unmapped, and look like a de novo insertion in the child. This script cuts the trio's reads
at those places from the public CRAMs, fetches the two bacterial genomes, and writes down which of the child's read
pairs are the bacterium's by alignment - the set every version of interloper has to get right.

Steps (each writes under tests/data/, and each can be run again):

  cut       the reads of child, father and mother at each place, 1,000 bp either side, mates included wherever they
            map: primary records, not marked duplicate or QC-fail, each read as it was sequenced, complete pairs only,
            sorted by name                                              -> litmus/<trio>/<locus>/<role>.r{1,2}.fq.gz
  human     the GRCh38 sequence at each place, 5,000 bp either side     -> genomes/GRCh38.litmus_loci.fa.gz
  genomes   the two RefSeq genomes from NCBI Datasets, checked against the md5 NCBI ships with them
                                                                        -> genomes/<accession>.fna.gz
  truth     each member's pairs aligned to the trio's bacterium (minimap2 -ax sr --secondary=no): an END is the
            bacterium's when it aligns over >= 90% of its length at >= 98% identity (1 - NM / aligned read bases)
                                                                        -> litmus/truth.tsv, litmus/truth_summary.tsv
  manifest  every file above with its size, md5, record count and source -> MANIFEST.tsv

  python3 tests/data/make_litmus.py all --ref GRCh38_full_analysis_set_plus_decoy_hla.fa

--ref is the reference the 1000 Genomes CRAMs are aligned to (with its .fai): it decodes them, and `human` is cut
from it. It is published at
https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.fa
Needs samtools >= 1.15 (view --fetch-pairs) and minimap2 on PATH, and network access to the 1000 Genomes S3 mirror
and to NCBI. Standard library otherwise. Nothing here reads anything but public files.
"""
import argparse
import csv
import gzip
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
S3 = "https://1000genomes.s3.amazonaws.com/1000G_2504_high_coverage"
PAD = 1000            # bp either side of a place that the reads are cut from
HUMAN_PAD = 5000      # bp either side of a place in the human reference slice
MIN_ALIGNED, MIN_IDENTITY = 0.90, 0.98      # the rule: an end is the organism's
TRUTH_MINIMAP2 = "2.30-r1287"               # the minimap2 the committed truth tables were derived with
DATASETS = "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/%s/download?include_annotation_type=GENOME_FASTA"

# The places are 0-based half-open regions on GRCh38, as the screen that found them reported them
# (kmer_denovo_filter discovery mode; docs/validation.md has the history).
TRIOS = {
    "HG01376": {
        "organism": "Methylobacterium organophilum", "strain": "WPA_B", "assembly": "GCF_022533465.1",
        "fasta_md5": "7daa4783ff299e27cc33507e5254881c",
        "members": {
            "child": ("HG01376", "ERR3988878", S3 + "/additional_698_related/data/ERR3988878/HG01376.final.cram"),
            "father": ("HG01374", "ERR3241894", S3 + "/data/ERR3241894/HG01374.final.cram"),
            "mother": ("HG01375", "ERR3241895", S3 + "/data/ERR3241895/HG01375.final.cram"),
        },
        "loci": [
            ("NDUFV1", "chr11", 67609473, 67609515),
            ("NDUFS7", "chr19", 1391114, 1391162),
            ("HSPA2", "chr14", 64542023, 64542072),
            ("SDHB", "chr1", 17024000, 17024074),
            ("HSPA1A", "chr6", 31817141, 31817235),
            # bacterial by the screen's kraken2 labels (order Hyphomicrobiales), and NOT this genome: a flag without a name
            ("chrX_unnamed", "chrX", 101276417, 101276476),
        ],
    },
    "NA18521": {
        "organism": "Staphylococcus epidermidis", "strain": "ATCC 14990", "assembly": "GCF_006094375.1",
        "fasta_md5": "d2cf5ee3317b277783a33a4d976726ec",
        "members": {
            "child": ("NA18521", "ERR3989352", S3 + "/additional_698_related/data/ERR3989352/NA18521.final.cram"),
            "father": ("NA18522", "ERR3239351", S3 + "/data/ERR3239351/NA18522.final.cram"),
            "mother": ("NA18523", "ERR3239352", S3 + "/data/ERR3239352/NA18523.final.cram"),
        },
        "loci": [
            ("chr3_AT_rich", "chr3", 43711461, 43711496),
            ("chr4_AT_rich", "chr4", 176606530, 176606560),
            ("tRNA_Lys_chr11", "chr11", 122559953, 122559994),
            ("tRNA_Lys_chr16", "chr16", 73478341, 73478382),
        ],
    },
}
ROLES = ("child", "father", "mother")
_REVCOMP = str.maketrans("ACGTNacgtn", "TGCANtgcan")
_CIGAR = re.compile(r"(\d+)([MIDNSHP=X])")


def say(text):
    sys.stderr.write(text + "\n")
    sys.stderr.flush()


def region_of(chrom, start, end, pad):
    """A 0-based half-open place as a 1-based samtools region, padded."""
    return "%s:%d-%d" % (chrom, max(1, start + 1 - pad), end + pad)


def write_gz(path, text):
    """Gzip text with no time and no name in the header, so the same reads make the same file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as gz:
            gz.write(text.encode())
    os.replace(path + ".tmp", path)


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def md5_gz_content(path):
    h = hashlib.md5()
    with gzip.open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fastq_names(path):
    with gzip.open(path, "rt") as fh:
        return [line[1:].rstrip("\n") for i, line in enumerate(fh) if i % 4 == 0]


# ---------------------------------------------------------------------------------------------------------------- cut
def cut_pairs(url, region, ref, samtools="samtools"):
    """The complete read pairs with an end in the region, as sequenced: {name: [(seq, qual), (seq, qual)]}, and how
    many reads had no mate among the records. Primary records only, duplicates and QC failures left out."""
    with tempfile.TemporaryDirectory() as work:          # samtools keeps a remote file's index where it runs
        done = subprocess.run([samtools, "view", "-T", ref, "--fetch-pairs", "-F", "0xF00", url, region],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=work)
    if done.returncode != 0:
        raise RuntimeError("samtools view %s %s: %s" % (url, region, done.stderr.strip()[-400:]))
    ends = {}
    for line in done.stdout.splitlines():
        f = line.split("\t")
        flag = int(f[1])
        if not flag & 0x1 or f[9] == "*":
            continue
        seq, qual = f[9], f[10]
        if flag & 0x10:
            seq, qual = seq.translate(_REVCOMP)[::-1], qual[::-1]
        ends.setdefault(f[0], {})[1 if flag & 0x40 else 2] = (seq, qual)
    pairs = dict((n, [e[1], e[2]]) for n, e in ends.items() if 1 in e and 2 in e)
    return pairs, len(ends) - len(pairs)


def cut(args):
    for trio, t in TRIOS.items():
        for locus, chrom, start, end in t["loci"]:
            region = region_of(chrom, start, end, PAD)
            for role in ROLES:
                sample, run, url = t["members"][role]
                out = os.path.join(HERE, "litmus", trio, locus, role)
                if os.path.exists(out + ".r1.fq.gz") and os.path.exists(out + ".r2.fq.gz") and not args.force:
                    continue
                pairs, single = cut_pairs(url, region, args.ref, args.samtools)
                for k in (0, 1):
                    write_gz("%s.r%d.fq.gz" % (out, k + 1),
                             "".join("@%s\n%s\n+\n%s\n" % (n, pairs[n][k][0], pairs[n][k][1]) for n in sorted(pairs)))
                say("cut %s %s %s (%s %s): %d pairs, %d reads without their mate left out"
                    % (trio, locus, role, sample, region, len(pairs), single))


def human(args):
    """The reference at every place, HUMAN_PAD either side: what a read placed there is compared with."""
    records = []
    for trio, t in TRIOS.items():
        for locus, chrom, start, end in t["loci"]:
            region = region_of(chrom, start, end, HUMAN_PAD)
            done = subprocess.run([args.samtools, "faidx", args.ref, region], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, universal_newlines=True)
            if done.returncode != 0:
                raise RuntimeError("samtools faidx %s: %s" % (region, done.stderr.strip()[-300:]))
            lines = done.stdout.splitlines()
            records.append(">%s %s %s GRCh38\n%s\n" % (region, trio, locus, "\n".join(lines[1:])))
    write_gz(os.path.join(HERE, "genomes", "GRCh38.litmus_loci.fa.gz"), "".join(records))
    say("human: %d places, %d bp either side" % (len(records), HUMAN_PAD))


# ------------------------------------------------------------------------------------------------------------ genomes
def genomes(args):
    for trio, t in TRIOS.items():
        acc = t["assembly"]
        out = os.path.join(HERE, "genomes", acc + ".fna.gz")
        if os.path.exists(out) and not args.force:
            continue
        with tempfile.TemporaryDirectory() as work:
            archive = os.path.join(work, acc + ".zip")
            with urllib.request.urlopen(urllib.request.Request(DATASETS % acc, headers={"User-Agent": "interloper-tests"})) as r, \
                    open(archive, "wb") as fh:
                shutil.copyfileobj(r, fh)
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                fna = [n for n in names if n.endswith(".fna") and acc in n]
                if len(fna) != 1:
                    raise RuntimeError("%s: expected one .fna in the archive, found %s" % (acc, fna))
                data = z.read(fna[0])
                sums = z.read("md5sum.txt").decode() if "md5sum.txt" in names else ""
        md5 = hashlib.md5(data).hexdigest()
        shipped = [line.split()[0] for line in sums.splitlines() if line.strip().endswith(os.path.basename(fna[0]))]
        if shipped and shipped[0] != md5:
            raise RuntimeError("%s: md5 %s, NCBI's md5sum.txt says %s" % (acc, md5, shipped[0]))
        if md5 != t["fasta_md5"]:
            raise RuntimeError("%s: md5 %s is not the genome this set was built on (%s)" % (acc, md5, t["fasta_md5"]))
        write_gz(out, data.decode())
        say("genome %s (%s %s): %d bytes, md5 %s" % (acc, t["organism"], t["strain"], len(data), md5))


# -------------------------------------------------------------------------------------------------------------- truth
def align_pairs(genome, r1, r2, minimap2="minimap2", threads=2):
    """Each read end's primary alignment to the genome: {name: {1: end, 2: end}}, an end a dict of aligned (the share
    of its bases in the alignment), identity (1 - NM / aligned read bases), proper (the pair is a proper pair) and
    tlen; an unaligned end has aligned 0 and identity None."""
    done = subprocess.run([minimap2, "-ax", "sr", "--secondary=no", "-t", str(threads), genome, r1, r2],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if done.returncode != 0:
        raise RuntimeError("minimap2 %s: %s" % (genome, done.stderr.strip()[-400:]))
    ends = {}
    for line in done.stdout.splitlines():
        if line.startswith("@"):
            continue
        f = line.split("\t")
        flag = int(f[1])
        if flag & 0x900:
            continue
        which = 1 if flag & 0x40 else 2
        length = len(f[9])
        if flag & 0x4 or f[5] == "*":
            end = {"aligned": 0.0, "identity": None, "proper": False, "tlen": 0}
        else:
            ops = _CIGAR.findall(f[5])
            length = sum(int(n) for n, op in ops if op in "MIS=XH")
            bases = sum(int(n) for n, op in ops if op in "MI=X")
            nm = next((int(x[5:]) for x in f[11:] if x.startswith("NM:i:")), 0)
            end = {"aligned": float(bases) / length if length else 0.0, "identity": (1.0 - float(nm) / bases) if bases else None,
                   "proper": bool(flag & 0x2), "tlen": abs(int(f[8]))}
        ends.setdefault(f[0], {})[which] = end
    return ends


def passes(end):
    return end is not None and end["identity"] is not None and end["aligned"] >= MIN_ALIGNED and end["identity"] >= MIN_IDENTITY


def derive_truth(minimap2="minimap2", threads=2):
    """(rows of truth.tsv, rows of truth_summary.tsv), from the files on disk. A child's molecule is listed when an
    end of it aligns to the trio's genome over MIN_ALIGNED of its length (whatever its identity, so that an end just
    under the identity rule is seen for what it is)."""
    truth, summary = [], []
    with tempfile.TemporaryDirectory() as work:
        for trio, t in TRIOS.items():
            genome = os.path.join(work, t["assembly"] + ".fna")
            with gzip.open(os.path.join(HERE, "genomes", t["assembly"] + ".fna.gz"), "rb") as src, open(genome, "wb") as dst:
                shutil.copyfileobj(src, dst)
            for locus, chrom, start, end in t["loci"]:
                for role in ROLES:
                    sample = t["members"][role][0]
                    base = os.path.join(HERE, "litmus", trio, locus, role)
                    ends = align_pairs(genome, base + ".r1.fq.gz", base + ".r2.fq.gz", minimap2, threads)
                    n_pass = sum(1 for e in ends.values() for k in (1, 2) if passes(e.get(k)))
                    both = sum(1 for e in ends.values() if passes(e.get(1)) and passes(e.get(2)))
                    summary.append([trio, locus, "%s:%d-%d" % (chrom, start, end), role, sample, t["organism"], t["assembly"],
                                    len(ends), 2 * len(ends), n_pass, both])
                    if role != "child":
                        continue
                    for name in sorted(ends):
                        e = ends[name]
                        if not any(e.get(k) and e[k]["aligned"] >= MIN_ALIGNED for k in (1, 2)):
                            continue
                        row = [trio, sample, locus, "%s:%d-%d" % (chrom, start, end), name, t["organism"], t["assembly"]]
                        for k in (1, 2):
                            x = e.get(k) or {"aligned": 0.0, "identity": None}
                            row += ["%.3f" % x["aligned"], "." if x["identity"] is None else "%.4f" % x["identity"]]
                        row += [sum(1 for k in (1, 2) if passes(e.get(k))), int(bool(e.get(1) and e[1]["proper"])),
                                (e.get(1) or {}).get("tlen", 0)]
                        truth.append(row)
    return truth, summary


TRUTH_HEADER = ["trio", "sample", "locus", "grch38_region", "molecule", "organism", "assembly", "end1_aligned", "end1_identity",
                "end2_aligned", "end2_identity", "ends_passing", "proper_pair", "insert"]
SUMMARY_HEADER = ["trio", "locus", "grch38_region", "role", "sample", "organism", "assembly", "pairs", "read_ends",
                  "ends_passing", "molecules_both_ends_passing"]


def write_tsv(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def truth(args):
    rows, summary = derive_truth(args.minimap2, args.threads)
    write_tsv(os.path.join(HERE, "litmus", "truth.tsv"), TRUTH_HEADER, rows)
    write_tsv(os.path.join(HERE, "litmus", "truth_summary.tsv"), SUMMARY_HEADER, summary)
    for trio in TRIOS:
        mine = [r for r in rows if r[0] == trio]
        say("truth %s: %d of the child's molecules reach the genome, %d read ends pass the rule; the parents' ends that pass: %d"
            % (trio, len(mine), sum(r[11] for r in mine), sum(s[9] for s in summary if s[0] == trio and s[3] != "child")))


# ----------------------------------------------------------------------------------------------------------- manifest
MANIFEST_HEADER = ["path", "bytes", "md5", "content_md5", "records", "kind", "source", "region", "made_by"]


def manifest(args):
    rows = []
    for trio, t in TRIOS.items():
        for locus, chrom, start, end in t["loci"]:
            for role in ROLES:
                sample, run, url = t["members"][role]
                for k in (1, 2):
                    rel = "litmus/%s/%s/%s.r%d.fq.gz" % (trio, locus, role, k)
                    p = os.path.join(HERE, rel)
                    rows.append([rel, os.path.getsize(p), md5_file(p), md5_gz_content(p), len(fastq_names(p)),
                                 "reads, end %d (%s, %s, %s)" % (k, sample, run, role), url, region_of(chrom, start, end, PAD),
                                 "make_litmus.py cut"])
    for trio, t in TRIOS.items():
        rel = "genomes/%s.fna.gz" % t["assembly"]
        p = os.path.join(HERE, rel)
        with gzip.open(p, "rt") as fh:
            n = sum(1 for line in fh if line.startswith(">"))
        rows.append([rel, os.path.getsize(p), md5_file(p), md5_gz_content(p), n, "genome (%s %s)" % (t["organism"], t["strain"]),
                     DATASETS % t["assembly"], ".", "make_litmus.py genomes"])
    rel = "genomes/GRCh38.litmus_loci.fa.gz"
    p = os.path.join(HERE, rel)
    with gzip.open(p, "rt") as fh:
        n = sum(1 for line in fh if line.startswith(">"))
    rows.append([rel, os.path.getsize(p), md5_file(p), md5_gz_content(p), n, "human reference at the places",
                 "GRCh38_full_analysis_set_plus_decoy_hla.fa", "each place +/- %d bp" % HUMAN_PAD, "make_litmus.py human"])
    for rel in ("litmus/truth.tsv", "litmus/truth_summary.tsv"):
        p = os.path.join(HERE, rel)
        with open(p) as fh:
            n = sum(1 for _ in fh) - 1
        rows.append([rel, os.path.getsize(p), md5_file(p), md5_file(p), n, "truth by alignment", ".", ".", "make_litmus.py truth"])
    write_tsv(os.path.join(HERE, "MANIFEST.tsv"), MANIFEST_HEADER, rows)
    say("manifest: %d files, %d bytes" % (len(rows), sum(r[1] for r in rows)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=("cut", "human", "genomes", "truth", "manifest", "all"))
    parser.add_argument("--ref", help="GRCh38_full_analysis_set_plus_decoy_hla.fa, indexed (cut, human)")
    parser.add_argument("--samtools", default="samtools")
    parser.add_argument("--minimap2", default="minimap2")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--force", action="store_true", help="make again what is already there")
    args = parser.parse_args(argv)
    steps = ("cut", "human", "genomes", "truth", "manifest") if args.step == "all" else (args.step,)
    if ("cut" in steps or "human" in steps) and not (args.ref and os.path.isfile(args.ref + ".fai")):
        parser.error("--ref (with its .fai) is needed for cut and human")
    for step in steps:
        {"cut": cut, "human": human, "genomes": genomes, "truth": truth, "manifest": manifest}[step](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
