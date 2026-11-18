# Validation

What has to be shown before any result of interloper is believed, on what data, and what counts as passing. The
criteria are written down here before the method exists, so that the method is built to meet them and not the other
way round.

Only public data is used: for the tests, for the benchmark, and for setting every threshold.

## 1. What has to be shown

| Claim | Shown by |
| --- | --- |
| A contaminated library's organism is named, and confirmed as a genome in the library | the two litmus libraries (section 2); spike-ins (section 6) |
| The reads behind a false variant are assigned to that organism | the litmus molecules: 96 of them, listed |
| Human reads are never assigned to it | the parents' reads at the same places: 11,472 read ends; the children's own human reads there |
| A wrong label on human sequence does not become a finding | the label counterexamples (section 4) |
| A real variant's reads come out human | structural variants the child's own long reads carry (section 4) |
| What cannot be named is reported as unexplained | the chrX place of HG01376 (section 2) |
| It works for organisms nobody has caught in real data here | spike-ins, including animals and plants (section 6) |

## 2. The litmus set (in this repository)

Two children of the 1000 Genomes high-coverage trios whose sequencing library holds a bacterium's DNA and whose
parents' libraries do not. In each trio the child's library was made and sequenced about a year after the parents'.

| | HG01376 | NA18521 |
| --- | --- | --- |
| Trio (father, mother) | HG01374, HG01375 | NA18522, NA18523 |
| Runs (child; father; mother) | ERR3988878; ERR3241894; ERR3241895 | ERR3989352; ERR3239351; ERR3239352 |
| Organism | *Methylobacterium organophilum* | *Staphylococcus epidermidis* |
| Assembly | GCF_022533465.1 (strain WPA_B) | GCF_006094375.1 (ATCC 14990) |
| Places on GRCh38 | 5, and one unnamed | 4 |
| Human sequence at the places | NDUFV1, NDUFS7, HSPA2, SDHB, HSPA1A: genes with a bacterial ortholog | a tRNA-Lys gene (two identical copies), two AT-rich stretches |

At each place a k-mer screen for de novo structural variants (kmer_denovo_filter, discovery mode) reported a
candidate in the child, an insertion where it was typed: clipped reads stacked on 30 to 49 matching bases, mates
unmapped, nothing in either parent.

**What is committed** (`tests/data/`, 65 files, 2.9 MB; `MANIFEST.tsv` lists each with its size, md5, record count
and source):

* `litmus/<trio>/<place>/<role>.r{1,2}.fq.gz`: every read pair of child, father and mother with an end within
  1,000 bp of the place, mates included wherever they map, as sequenced. Primary records; duplicates and QC failures
  left out.
* `genomes/`: the two bacterial genomes (RefSeq, md5 as NCBI ships them) and the GRCh38 sequence 5,000 bp either
  side of each place.
* `litmus/truth.tsv`, `litmus/truth_summary.tsv`: which of the child's molecules are the bacterium's, by alignment.

**How it was made.** `tests/data/make_litmus.py` cuts the reads from the public CRAMs on the 1000 Genomes S3 mirror,
fetches the genomes from NCBI Datasets, and derives the truth. It reads nothing but public files, and anyone can run
it again:

```bash
python3 tests/data/make_litmus.py all --ref GRCh38_full_analysis_set_plus_decoy_hla.fa
```

**The truth, and the rule it rests on.** Each member's pairs were aligned to the trio's bacterium
(`minimap2 -ax sr --secondary=no`). A read end is the bacterium's when it aligns over at least 90% of its length at
98% identity or more.

| Trio | Place | Child's molecules that are the bacterium's | Their read ends passing | Parents' read ends passing |
| --- | --- | --- | --- | --- |
| HG01376 | NDUFV1, chr11:67,609,473 | 14 | 28 of 28 | 0 of 1,166 |
| HG01376 | NDUFS7, chr19:1,391,114 | 9 | 18 of 18 | 0 of 1,370 |
| HG01376 | HSPA2, chr14:64,542,023 | 13 | 26 of 26 | 0 of 1,174 |
| HG01376 | SDHB, chr1:17,024,000 | 9 | 18 of 18 | 0 of 1,214 |
| HG01376 | HSPA1A, chr6:31,817,141 | 8 | 16 of 16 | 0 of 1,494 |
| HG01376 | unnamed, chrX:101,276,417 | 0 | 0 | 0 of 726 |
| NA18521 | AT-rich, chr3:43,711,461 | 6 | 12 of 12 | 0 of 1,048 |
| NA18521 | AT-rich, chr4:176,606,530 | 9 | 17 of 18 | 0 of 1,128 |
| NA18521 | tRNA-Lys, chr11:122,559,953 | 14 | 28 of 28 | 0 of 1,062 |
| NA18521 | tRNA-Lys, chr16:73,478,341 | 14 | 28 of 28 | 0 of 1,090 |
| | **all** | **96** | **191 of 192** | **0 of 11,472** |

Three things in the table are tests in their own right:

* **One end at 97.3%.** One molecule at NA18521's chr4 place has an end aligned over its whole length at 97.3%
  identity, just under the rule. Its other end passes and the two are a proper pair. A rule on single ends misses
  it; a rule on molecules must not.
* **The unnamed place.** At chrX:101,276,417 the screen's kraken2 labels called 8 of 8 supporting read ends
  bacterial, to the order that holds *Methylobacterium*. Not one of the child's 592 read ends there aligns to
  *M. organophilum*. The right answer is "bacterial by label, no genome named": a flag, not a finding.
* **More than the screen saw.** The screen's candidates at HSPA2 and HSPA1A rested on 6 and 5 molecules; the cut
  holds 13 and 8 that are the bacterium's. Reads that carry no child-only k-mer, or lie further from the candidate,
  are the bacterium's all the same.

**What runs today.** `tests/test_litmus.py` checks the files against the manifest and, where minimap2 is installed,
runs the rule again on the reads: the same molecules, and no read end of a parent. This is the method's premise on
real data, checked before any of the method is written.

**Independent of the reads.** Neither contaminated child has been sequenced a second time, but relatives have, on
long reads. At HG01376's six places, 98 of its mother's 105 nanopore reads run straight through and none carries an
insertion. At NA18521's four, its father's assembly runs straight through each, as do 51 of its mother's 73 nanopore
reads, with no junction in any. The places are ordinary human sequence in the family; what is unusual is in one
library.

## 3. What each stage must do on the litmus set

| Stage | Passing |
| --- | --- |
| 2, name | from a screen of each child's reads, the two assemblies above are named (species right; this strain or a close one) |
| 3, verify the library | each is **present** in its child, and **not confirmed** in either parent; reads over the whole chromosome, the same share in every lane |
| 4, assign | all 96 molecules FOREIGN with the right genome; none of the parents' 11,472 read ends FOREIGN; the children's other reads at the places HUMAN |
| 5, judge | the 9 named places **foreign**; the chrX place **unexplained**, with its label reported |
| any | a missing database, a failed alignment or an unreachable genome ends in an error, never in "clean" |

The library-level stages need more of each library than the places: a deterministic sample of each member's
unmapped pairs, cut the same way, is the next addition to the set ([roadmap.md](roadmap.md), M2).

## 4. To add to the set: where labels are wrong, and where variants are real

Both come from the same cohort, both are public, and neither is cut yet.

**Labels on human sequence.** Reads a k-mer classifier calls bacterial that are human. Each recurs at one human
place across many children whose libraries hold almost no bacterial DNA:

| Label (kraken2, PrackenDB) | Human place | Children |
| --- | --- | --- |
| *Rhodobacter flavimaris* | the immunoglobulin heavy-chain locus, chr14:105.9-106.8 Mb, and the contigs joined to it | 33 |
| *Alteribacter natronophilus* | chr9:137.1 Mb and the decoy contigs joined to it | 61 |
| Pseudomonadota and others | the mitochondrial genome | 315 |
| fungi, protists | human repeats, about 17,500 regions | 595 |

Passing: these reads are HUMAN or AMBIGUOUS, never FOREIGN; no genome is confirmed in the library; and stage 6
lists each label as recurring at one place.

**Real variants.** In the same screen, 58 structural variants are carried by the child's own long reads and by no
parent's: deletions, duplications, inversions and breakends from 687 bp to 8 Mb. Passing: their supporting reads
are HUMAN on both sides of the junction, and the verdict is human-supported. A handful with assemblies that hold
them are the first to cut (for example a 1.4 kb deletion in HG00408 at chr5:171,578,322, a 496 kb duplication in
HG03710 at chr11:1,884,262, an 8.0 Mb inversion in HG03516 at chr10:24,715,016).

**Two more libraries.** HG02735 has one region made of bacterial reads that kraken2 labels *Neisseria sicca*, and no
genome has been named for it yet: a test of stage 2. HG02575 and HG01508 hold 14.5% and 13.5% bacterial reads and no
region made of them: a profile without an event.

## 5. The cohort these come from

The numbers in sections 2 and 4, and in [design.md](design.md), come from one screen: kmer_denovo_filter discovery
mode (k = 31) on 597 trios of the 1000 Genomes high-coverage data, with kraken2 2.17.1 on PrackenDB
(`k2_NCBI_reference_20251007`, confidence 0.1) labelling each candidate region's reads, and a flag at 5% non-human
of at least 5 classified reads. In summary:

* The children's bacterial share of the sampled reads has a median of 0.01%. Five are above 5%: HG01376 57.6%,
  NA18521 26.0%, HG02575 14.5%, HG01508 13.5%, HG02735 6.7%.
* HG01376: 291,335 of 537,422 screened read ends align to *M. organophilum*. Only 279 touched the human reference,
  at 225 places, and five places gathered the three reads a region needs. NA18521: 96,950 of 394,660, 133 touching
  the reference at 93 places, four gathering three.
* The flag marked 36,723 regions. 11 are made of bacterial reads. 143 are human sequence under a recurring
  bacterial label. About 17,500 carry fungal or protist labels and no bacterial read; of the 3,213 of those that are
  assembled in the child's own long-read assembly, 2,262 (70%) hold a structural allele of 50 bp or more within
  200 bp.
* Every region made of bacterial reads is shorter than one read on the reference (30 to 94 bp) and has no split
  read, discordant pair or junction.

Section 2's reads are reproduced in this repository. The cohort-wide counts are not yet: they were produced
outside it, and reproducing them here from public files is a milestone of its own ([roadmap.md](roadmap.md), M5).
Until then they are context, not results of interloper.

1000 Genomes data are used here as a reference cohort of public genomes. No comparison with any other cohort is
made or implied.

## 6. Spike-ins

The two real libraries are bacterial, were found by the method this one replaces, and come from cell-line DNA. They
show that interloper is no worse. What they cannot show is tested with reads of known origin mixed into real human
reads:

| Varied | Values | Asks |
| --- | --- | --- |
| Organism | mouth bacteria; reagent and water-system bacteria; a fungus; a virus; **a food animal, a pet, a laboratory animal; a food plant** | is each named, confirmed and assigned |
| Share of the library | from one read in a million to half | where naming and confirmation stop working |
| Distance from the panel's genome | the same strain; another strain; another species of the genus | does "relative of" appear where it should, and "unexplained" beyond it |
| Reads engineered to land on human | bacterial and animal reads with a 20 to 60 base exact human anchor | the mechanism of section 2, at will |
| Traps | human reads that a non-human assembly holds a copy of; human reads absent from the reference but present in a telomere-to-telomere assembly; adapter read-through | AMBIGUOUS, HUMAN and SYNTHETIC, never FOREIGN |

Reads are simulated from public assemblies with a stated error model and seed; the human background is a public
genome's own reads. Each spike-in is a manifest row, like the litmus files.

## 7. Criteria, fixed in advance

| | Criterion |
| --- | --- |
| Litmus molecules | 96 of 96 FOREIGN with the right genome |
| Parents' and children's human reads at the places | 0 FOREIGN |
| Label counterexamples | 0 FOREIGN; 0 genomes confirmed |
| Real variants | every one human-supported |
| Spike-in, same strain, at one read in ten thousand or more | named, confirmed, and at least 95% of its reads assigned |
| Spike-in, human reads of any kind | at most one in a million assigned FOREIGN |
| Traps | 0 FOREIGN |
| A failure anywhere | a non-zero exit and a message; never an empty, clean-looking output |

The two spike-in numbers are proposals for review, not measurements.

## 8. What this plan cannot show

* **No mouth-derived truth set yet.** The motivating use is DNA from buccal swabs and saliva. The real libraries here
  are cell-line DNA with a laboratory contaminant. Mouth bacteria, food and animal DNA are covered by spike-ins
  alone until a public mouth-derived data set with an independent truth is in the set. The literature offers two
  leads ([roadmap.md](roadmap.md), question 12): matched blood, saliva and buccal genomes of the same people, and a
  public saliva genome with a large share of plant reads. Neither has been checked for access.
* **Truth by alignment is the method's own kind of evidence.** The litmus truth is "aligns to the named genome".
  The long reads of relatives say the places are ordinary in the family; they do not sequence the contaminated
  library again.
* **Thresholds set on two libraries are set on two libraries.** The rule's 90% and 98% come from these reads. The
  spike-ins' distance axis is there to find where they stop holding.

## Data

1000 Genomes high-coverage sequencing: Byrska-Bishop et al., Cell 2022 ([prior-art.md](prior-art.md)). The CRAMs
are on the project's public S3 mirror and at the European Nucleotide Archive under the run accessions above. The
bacterial genomes are NCBI RefSeq assemblies.
