# Roadmap, and the questions open for review

## Milestones

Each milestone ends with a row of [validation.md](validation.md) passing in CI. Nothing is called done on the
strength of having been written.

| | What | Done when |
| --- | --- | --- |
| **M0** | Groundwork: the design, the prior work, the database survey, the validation plan; the container; the litmus reads with their rule run again in CI | this commit |
| **M1** | External review of the design and of the questions below; the design revised | the questions below each have an answer or an experiment |
| **M2** | The library stages (screen, name, verify) on the two litmus libraries; the set extended with a sample of each member's unmapped pairs | validation.md section 3, rows "name" and "verify" |
| **M3** | The read and event stages (assign, events); the label counterexamples and the real variants cut into the set | section 3, rows "assign" and "judge"; section 7's first four rows |
| **M4** | The spike-in harness; thresholds set on it; the eukaryote panel, first version | section 7's spike-in and trap rows |
| **M5** | The cohort benchmark: the 597 trios' counts reproduced from public files; stage 6 (curate); the two reusable tables | validation.md section 5 reproduced by a command in this repository |
| **M6** | Use from kmer_denovo_filter; release 0.1.0; a guide to mouth-derived DNA and its pitfalls | a pipeline run on public data from the image alone |

## Questions for review

Numbered so that a review can answer them one by one. Each says what was assumed, so that the assumption can be
attacked.

**Prior work**

1. **Has per-candidate read provenance been done?** A search found no published method whose purpose is to decide,
   for the reads supporting a candidate variant, whether they are non-human ([prior-art.md](prior-art.md), section
   9). Is that right, or was something missed, under another name or in another field (ancient DNA, forensic,
   xenograft, metagenome-assembled genomes)?
2. **A decoy at alignment, or assignment after it?** The published remedy for mouth bacteria in human genomes is to
   add bacterial genomes to the reference before alignment, so that their reads go there (Samson 2020; An 2025, with
   metagenome-assembled genomes). interloper compares alignments afterwards, for the supporting reads only, with
   genomes named from the library itself. Is there a case where the decoy does strictly better? Should interloper
   also write the confirmed panel as a decoy FASTA, for pipelines that can realign?

**The rules**

3. **Is the explained fraction the right statistic?** `e = (aligned read bases - edit distance) / read length`,
   compared between the human set and the panel, with thresholds 0.88, 0.10 and 0.95. The xenograft tools compare
   alignment scores or edit distances directly. What does a single normalised number lose (indels, clipping at
   low-quality ends, reads of different lengths)?
4. **What makes a genome "present" at low depth?** Breadth against `1 - exp(-depth)` separates a genome from a pile
   of reads when there are thousands of reads. At a hundred reads the two are nearly the same number. Is a count of
   distinct windows hit, or of distinct minimizers against reads (the KrakenUniq idea), the better test there, and
   what is the smallest read count at which "present" should be said at all?
5. **One genome for a species?** A contaminant is rarely the reference strain. When its reads align at 92% and not
   99%, is the right move a second genome, a species pangenome, or the honest label "relative of"? Where does a
   relative end and "unexplained" begin?
6. **How should an event be judged from counts?** "At least three supporting molecules, most of them foreign, of
   one genome" is a rule of thumb. Is there a likelihood statement that is better and still explainable in a
   sentence?
7. **What supports a candidate, for a caller that does not say?** kmer_denovo_filter names its supporting reads.
   For other structural-variant callers the proposal is clipped, split and discordant reads within a window. Is
   there a definition that is fair across callers?

**The databases**

8. **Why does PrackenDB label human sequence as two particular bacteria?** *Rhodobacter flavimaris* at the
   immunoglobulin heavy-chain locus and *Alteribacter natronophilus* at one stretch of chr9, each in dozens of
   samples. Human sequence inside those reference assemblies, or k-mers shared by chance in GC-rich sequence? The
   experiment is cheap (align the human places to the two assemblies; run a foreign-sequence screen on them) and
   belongs in M2.
9. **Which eukaryotes go on the panel, and is "organelle first" sound?** The proposal is to detect animals and
   plants by their organelle genomes and confirm on the nuclear genome. One study reports food plants and animals
   among the reads that misalign in saliva genomes (Samson 2020); no study was found with that as its subject. Which
   species belong on the panel? And do nuclear copies of mitochondrial DNA, in human and in the other animal, break
   the organelle test?
10. **What is the human set, concretely?** Which telomere-to-telomere assembly, which pangenome release, and in
    what form is "pangenome sequence absent from the reference" best held for alignment?
11. **kraken2's distinct-minimizer report is marked experimental**, and is an estimate. Is it reliable on a
    database of this size, and is it available in the mode the screen uses? If not: count distinct minimizers from
    the per-read k-mer detail instead.

**The validation**

12. **Is there a public mouth-derived data set with a truth?** Saliva or buccal whole-genome sequencing with a
    matched blood sample, a family, or long reads of the same person. Two leads from the literature, neither checked
    for access yet: the matched blood, saliva and buccal genomes of four people (Trost 2019; used again by An 2025),
    and the public saliva genome that is dominated by a wheat relative (Samson 2020). Without one, mouth bacteria and
    food DNA rest on spike-ins ([validation.md](validation.md), section 8).
13. **Are the acceptance numbers the right ones?** 95% of a same-strain spike-in's reads assigned at one read in
    ten thousand; at most one human read in a million called foreign. Too strict, too loose, or the wrong
    quantities?
14. **What should count as synthetic?** Vectors, control spike-ins and adapters are named by the screen's vector
    set. A read that runs through its fragment into the adapter and the sample's own index is private to a library
    in the same way a contaminant is. In scope here, or a matter for read trimming upstream?

## Decisions for the maintainers

* Decided: the cohort-wide 1000 Genomes numbers ([validation.md](validation.md), section 5) are stated in this
  repository as context, marked as not yet reproduced here, until M5 reproduces them.
* The kraken2 release: the image pins v2.17.1, the release nonhuman-screen is tested against. 2.17.2 is out and
  2.18.0 is a release candidate; when to move is a decision for the two tools together.
* Whether nonhuman-screen stays an optional extra (`pip install interloper[screen]`) or becomes a hard dependency
  once stage 1 exists.
