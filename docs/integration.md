# Using interloper from a pipeline

How a variant-calling pipeline is expected to call interloper once the stages of [design.md](design.md) exist. The
interface is a proposal: it is fixed when the first stage is implemented, and changed here first.

## The container

One image, built by this repository's CI and published to the GitHub container registry:

```bash
# Docker
docker run --rm ghcr.io/jlanej/interloper:latest doctor

# Apptainer / Singularity on a cluster
apptainer build interloper.sif docker://ghcr.io/jlanej/interloper:latest
apptainer run interloper.sif doctor
```

The image holds kraken2, minimap2, samtools, nonhuman-screen and interloper. It holds no database and no genome.
`doctor` prints each tool's version and exits non-zero if one is missing, so a pipeline can check an image before it
uses it. Pin a release by its tag or its `sha-` tag, not `latest`.

## What a pipeline provides

| | |
| --- | --- |
| The sample's reads | BAM or CRAM with its reference, or FASTQ pairs |
| A database directory | the kraken2 database of [databases.md](databases.md), with its taxonomy files |
| A cache directory | where fetched genomes are kept; shared by every sample of a cohort; writable |
| Candidates (optional) | BED regions, BEDPE junctions or a VCF, and how their supporting reads are defined |
| Reads to screen (optional) | a BAM the pipeline already holds of reads the reference does not explain |

On a cluster, bind those into the container and nothing else. Compute nodes without network access use `--offline`
after one run of `interloper db fetch` and `interloper name` on a node that has it; the cache is then complete.

## With kmer_denovo_filter

[kmer_denovo_filter](https://github.com/jlanej/kmer_denovo_filter) already screens with kraken2 through
nonhuman-screen and writes a non-human fraction per variant and per region. interloper is meant to sit after it:

| kmer_denovo_filter writes | interloper reads it as |
| --- | --- |
| the informative reads' BAM (reads carrying child-only k-mers) | the reads to screen, and the supporting reads of each region |
| the regions BED and the junctions BEDPE | the candidates |
| the kraken2 screen's per-region record | the labels to verify |

and adds, per candidate, the classes of its supporting molecules, the genome named, and a verdict. The existing
non-human fraction stays what it is, a screen; nothing interloper writes replaces or renames a column that exists.

## With any other caller

The same three things: the reads, the candidates, and a rule for which reads support a candidate. For small variants
the rule nonhuman-screen uses - reads carrying the ALT allele - is taken as it is.

## What a pipeline should do with the verdict

interloper reports; the pipeline decides. A reasonable use: set aside a candidate whose verdict is **foreign**,
with the genome named in the output; carry **human-supported** as evidence for the candidate; and leave **mixed**
and **unexplained** to the pipeline's other evidence. A candidate is never dropped silently: the table keeps every
row with its counts.

## Controlled-access data

The tool sends no read anywhere. It downloads public genomes and databases, and with `--offline` not even those.
Its tables hold counts, genome accessions and verdicts; the one table with read names (`reads.tsv`) is optional.
What may leave a controlled-access environment is the data owner's decision, and the outputs are laid out so that
the cohort-level report can be shared without any per-read or per-sample table.
