# interloper: design

**Status: groundwork.** Nothing in this document is implemented yet except the litmus set
([validation.md](validation.md)) and the container. Every threshold below is a starting value with the data it is to
be calibrated on named beside it. The prior work each idea comes from is in [prior-art.md](prior-art.md).

## 1. The problem

A human sequencing library is not only human. DNA of other organisms reaches it from the tissue (the mouth's bacteria
in a buccal swab or saliva; food; other animals), from the bench (reagents, water systems, skin, cell-culture
contaminants) and from the instrument (control spike-ins, vectors, adapters). Most of that DNA never aligns to the
human reference and is ignored. A small part does, and that part is the problem.

**How a foreign read becomes a human variant.** In the two contaminated libraries of the litmus set, a bacterial
read pair comes from a gene with a human ortholog (complex I and II subunits, Hsp70, a tRNA) or from an AT-rich
stretch. Some 30 to 49 bases of one end match the human copy exactly or nearly; bwa-mem seeds on them, places the read
there - with a mapping quality of up to 60 where the human copy is unique - and soft-clips the other hundred bases.
The mate matches nothing human and stays unmapped. Clipped reads stacked at one place with unmapped mates are what an
insertion looks like. The same mechanism - short identical stretches flanked by soft clips - was described in saliva
genomes, where it changed genotype calls (Samson 2020, in [prior-art.md](prior-art.md)).

**Foreign DNA is private by construction.** Whatever entered one library and not the others looks like a variant
private to that sample. In a family design that is a de novo variant: no parent's reads hold it. A method that
subtracts the parents' sequence from the child's (a k-mer screen, a joint caller) cannot remove what the parents'
libraries never held. The same holds for any sample-against-cohort comparison.

**A label is not a proof.** The usual remedy is to classify reads taxonomically and flag a variant, or a region, by
the share of its reads labelled non-human. A k-mer classifier labels k-mers; it does not align reads, and its labels
are wrong in both directions often enough to matter. In the screen of 597 1000 Genomes trios that motivated this
tool ([validation.md](validation.md), section 5), a flag of that kind marked 36,723 regions:

* 11 of them were made of bacterial reads (two contaminated libraries and one more region);
* 143 carried bacterial labels on human sequence - one label recurring at one human place across dozens of children
  (the immunoglobulin heavy-chain locus, one stretch of chr9, the mitochondrial genome);
* about 17,500 carried fungal or protist labels and not one bacterial read, and where the same genomes have been
  assembled from long reads, 70% of those places hold a structural allele of the genome itself.

So the flag found the contamination, and buried it under human sequence with wrong names - much of it real
structural variation, which is what the screen was looking for.

## 2. The principle

Positive evidence at three levels, and an honest remainder.

| Level | The claim | What it takes |
| --- | --- | --- |
| **Organism** | "this organism's DNA is in this library" | a named genome, and the library's reads covering it the way a genome sampled at random is covered |
| **Read** | "this read is that organism's" | the read aligns to the named genome clearly better than to any human sequence |
| **Event** | "this candidate variant is that organism's reads" | the reads the candidate rests on are that organism's |

A read that no genome explains is **unexplained**, and is reported as that. It is never counted as foreign because a
classifier could not name it human, and never counted as human because a classifier could not name it foreign.

The burden of proof is symmetric. "Foreign" needs a genome that explains the read better than human does. "Human"
needs a human alignment that explains the whole read. A candidate variant stands on the second kind of evidence as
much as it falls on the first.

## 3. Terms

* **Read end**: one sequenced read of a pair. **Molecule**: the pair. Counts are of molecules unless they say ends.
* **Explained fraction** of a read end against a sequence set: the read's bases that its best alignment there
  matches, over the read's length: `e = (aligned read bases - edit distance) / read length`. A whole read aligned
  without a mismatch has `e = 1`; a 31-base exact anchor in a 150-base read has `e = 0.21`.
* **Human set**: every human sequence a read is compared with: the reference the data is aligned to (with its alts,
  decoys and HLA), a telomere-to-telomere assembly and pangenome sequence absent from the reference, and the
  mitochondrial genome. A read is not "non-human" because it is missing from one reference build.
* **Panel**: the non-human genomes a library's reads are compared with: those the screen names in this library and
  that the library check confirms, plus a small fixed set (vectors, control spike-ins).
* **Supporting reads** of a candidate: the reads the caller says the candidate rests on. interloper takes the
  caller's definition (section 6) and does not re-derive it.

## 4. The method

Six stages. The first is existing software; the rest are what this repository adds.

```
 reads ──▶ 1 screen ──▶ 2 name ──▶ 3 verify the library ──▶ sample profile
              │                          │ panel
              ▼                          ▼
 candidates ─────────────▶ 4 assign reads ──▶ 5 judge events ──▶ candidate table
                                                    │
                                 many samples ──▶ 6 curate ──▶ cohort report
```

### Stage 1. Screen (kraken2, through nonhuman-screen)

[nonhuman-screen](https://github.com/jlanej/nonhuman-screen) runs kraken2 on a set of reads and partitions them:
non-human by domain, human lineage (with its human-homology guard: a read with any k-mer voting human is never
counted non-human), vector and adapter sequence (UniVec Core), unclassified. It fails loudly when kraken2 fails.
interloper uses it as it is and needs one thing more from the kraken2 call: the per-taxon count of **distinct
minimizers** (kraken2's `--report-minimizer-data`), the idea of KrakenUniq built into kraken2. Many reads on few
distinct minimizers is one locus hit again and again; a genome that is present gives distinct minimizers in
proportion to its reads. nonhuman-screen discards kraken2's report today, so this is a small change there (keep the
report) and not a second classifier here.

The screen is a **screen**: it proposes names. Nothing downstream reports a label as a finding.

*What is screened.* A deterministic sample (by a hash of the read name) of the library's reads that the human
reference does not already explain: unmapped pairs, and pairs with an end that is clipped or poorly aligned. A caller
that already has such a set (kmer_denovo_filter's informative reads) passes it instead.

### Stage 2. Name the genomes

From the screen's report to a short list of assemblies:

1. Roll reads up to species. Keep the species that hold the bulk of the non-human reads (starting value: those
   reaching 0.5% of the labelled reads, at most 50), and any species at a candidate's supporting reads.
2. A label above species (a genus, "Bacteria") names nothing by itself: take the species below it with the most
   reads, or none.
3. For each species take one assembly: the RefSeq reference genome, else a representative genome. Fetch it from NCBI
   by accession, check it against the md5 NCBI ships, cache it. The accession and md5 are written into every output.

In the litmus set this is what turned "57.6% bacterial" into `GCF_022533465.1`, *Methylobacterium organophilum*
strain WPA_B.

### Stage 3. Verify the library

For each named genome, align the screened reads to it as pairs and ask whether a genome is there:

| Measure | What it says |
| --- | --- |
| Molecules whose ends are explained by the genome | how much of the library it is |
| Breadth against the breadth expected at that depth, `1 - exp(-depth)` | reads spread over the genome (an organism), or piled at a few places (a conserved gene, a contaminated contig, a plasmid alone) |
| Density per replicon | chromosome and plasmids in proportion |
| Identity of the explained ends (median, 5th centile) | this strain, a relative, or something else |
| Proper pairs and their insert sizes, against the library's human pairs | the same library, not a chimera of two |
| Share per read group or lane | in the library before sequencing (the same in every lane), or added by one run |

Verdict per genome: **present**, or **not confirmed** with the measure that failed. Only genomes that are present
enter the panel. A label whose genome is not confirmed stays a label, and is carried to stage 6, where recurrence
across samples tells a database artefact from a library.

In the litmus set: 291,335 of HG01376's 537,422 screened read ends are *M. organophilum* by alignment, over the whole
chromosome (53 per kb), a multi-copy plasmid at 352 per kb, 48% to 59% in each of 12 lanes, 90% of them without a
mismatch.

### Stage 4. Assign reads

For the reads of interest - a candidate's supporting reads with their mates - compare two alignments of each end:
its best in the human set (`e_h`) and its best in the panel (`e_f`, with the genome that gives it).

| Class | Rule (starting values) |
| --- | --- |
| **FOREIGN:genome** | `e_f >= 0.88` and `e_f - e_h >= 0.10` |
| **HUMAN** | `e_h >= 0.95` and `e_h >= e_f` |
| **AMBIGUOUS** | both at 0.88 or more, less than 0.10 apart: sequence conserved between the two, or one genome's sequence inside the other's assembly |
| **SYNTHETIC** | explained by a vector, adapter or control spike-in |
| **UNEXPLAINED** | none of the above |

`0.88` is the strict rule the litmus truth was established with - 90% of the end aligned at 98% identity - as one
number. A molecule takes the stronger class of its two ends when they agree or one is unexplained; a molecule with
one end foreign and the other human is **CHIMERIC**, and is reported, not resolved.

Two things the rule must survive, both in the validation plan: a contaminant that is a *relative* of the panel's
genome (its reads align at 92%, not 99%: the identity measured in stage 3 says so, and the class says "relative of"),
and a *human* read that a non-human assembly holds a copy of (it is AMBIGUOUS, never FOREIGN, because `e_h` is high).

### Stage 5. Judge events

Per candidate, the count of its supporting molecules in each class, and a verdict:

* **foreign** - enough supporting molecules (starting value: 3), and most of them FOREIGN, of one genome;
* **human-supported** - enough supporting molecules are HUMAN across the candidate's breakpoint: both sides of a
  junction, or the whole of a clipped read, explained by human sequence;
* **mixed**, **unexplained** - reported with the counts.

The verdict is about the reads the candidate rests on, not about every read near it. A wide region collects stray
reads; a junction's own reads are its evidence. A caller keeps its other evidence - depth across a deletion or
duplication, allele fractions inside it - and combines it with this one; interloper does not judge the event's
biology.

One observation from the litmus cohort belongs here: contamination made only short, point-like pseudo-insertions
(30 to 94 bp on the reference, clipped reads and unmapped mates, no junction). A deletion, duplication, inversion or
translocation needs human sequence on both sides of its breakpoint, and a foreign molecule has none to offer.

### Stage 6. Curate

Across samples: which organisms, in how many libraries, at what share; which human places their reads land on; and
which labels recur at one human place in many samples whose libraries hold no such organism - a label of the
database, not of any library. The output is a report a cohort can publish, and two reusable tables: the database
artefacts found (label, human place, samples) and the landing sites (organism gene, human place, anchor).

## 5. What is kraken2, and what is built here

kraken2 stays the k-mer engine: it is fast, standard, and databases for it are published. What is built here is
everything around it that turns a label into a finding - the distinct-minimizer evidence, the naming, the library
check, the competitive assignment, the event verdict - and the **database**: [databases.md](databases.md) sets out
why the published collections do not fit this use (the common ones hold no animal but human and no plant, so food
and other animals' DNA is invisible or mislabelled) and how a purpose-built one is assembled and pinned.

The stages after the screen do not depend on which screen proposed the names. If a containment sketch (sourmash,
Mash Screen) proves a better proposer on the benchmark, it replaces stage 1 without touching the rest.

## 6. Inputs and outputs

**Inputs.** A sample's BAM or CRAM with its reference (or FASTQ pairs); optionally a caller's set of reads to
screen; optionally candidates (BED regions, BEDPE junctions, or a VCF) with a rule for their supporting reads -
"reads named in this file", "reads carrying the ALT allele" (nonhuman-screen's definition), or "clipped, split and
discordant reads within N bp".

**Outputs.**

| File | One row per | Holds |
| --- | --- | --- |
| `profile.tsv` | named genome | accession, md5, reads and distinct minimizers from the screen, the stage 3 measures, the verdict |
| `sample.json` | sample | shares of the screened reads by class, the panel, tool and database versions, every threshold used |
| `reads.tsv` | supporting read end | class, genome, `e_h`, `e_f`, the human anchor (length, mapping quality), mate's class |
| `events.tsv` | candidate | supporting molecules by class, the leading genome, the verdict |
| `cohort/` | cohort | organisms by sample, database artefacts, landing sites, the report |

No output holds read sequence. Read names appear only in `reads.tsv`, which is optional.

## 7. Commands (planned)

```
interloper screen   --bam S.cram --ref R.fa --db DB        -> screen/ (kraken2 report with minimizer data, read labels)
interloper name     --screen screen/                       -> genomes.tsv (accession, md5), the cache filled
interloper verify   --bam S.cram --genomes genomes.tsv     -> profile.tsv, sample.json, the panel
interloper assign   --bam S.cram --candidates C --panel P  -> reads.tsv
interloper events   --reads reads.tsv --candidates C       -> events.tsv
interloper sample   ...                                    the five above in one call
interloper cohort   --samples samples.tsv                  -> cohort/
interloper db       build | fetch | check                  the database of databases.md
interloper doctor                                          the tools and their versions (exists today)
```

## 8. Rules the implementation keeps

* **A broken run never looks clean.** A failed screen, a genome that could not be fetched, an alignment that died:
  the output says so and the exit code is not 0. Nothing defaults to "no contamination".
* **Reads never leave the machine.** The only network use is downloading public genomes and databases, and
  `--offline` forbids even that (everything from the cache, or an error).
* **Everything is pinned and written down.** Tool versions, database name and date, each genome's accession and
  md5, each threshold: in `sample.json`.
* **The same input gives the same output.** Sampling by a hash of the read name, never a random draw.
* **Thresholds are data.** Each lives in one table with the benchmark that set it; none is tuned on anything but
  public data.

## 9. What it should cost

Per sample, as a budget to be measured, not a result: the screen on a few million reads is minutes and the memory of
the database; naming and fetching are seconds once cached; the library check is an alignment of those reads to tens
of small genomes; assignment touches only supporting reads. The large cost is the database's memory, which
[databases.md](databases.md) is about.

## 10. What it is not

* Not a variant caller, and not a variant filter: it reports where reads come from, and a caller decides.
* Not a detector of human-in-human contamination (another person's DNA): that needs genotypes, and tools for it
  exist.
* Not a microbiome profiler: it names what is in a library well enough to explain reads, and makes no claim about
  abundance in the tissue.
* Not a judge of an event's biology: depth and allele fractions across a deletion or duplication are the caller's
  evidence. They are strong evidence, and they are not about contamination.
