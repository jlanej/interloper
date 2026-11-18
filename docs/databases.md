# Databases

The screen (stage 1 of [design.md](design.md)) is as good as the database behind it, and no more. This page sets out
what the published kraken2 collections hold, why none of them fits this use as it stands, and what is proposed.

Facts about the published collections were read from the index page and from each collection's `inspect.txt` on
2026-11-18. Sizes are as the page lists them.

## What a database must hold for this use

1. **The human genome.** Without it nothing can vote human: the human-homology guard of nonhuman-screen never
   fires, and human reads are given to whatever shares their k-mers. This is the first error reported for the
   retracted cancer-microbiome study ([prior-art.md](prior-art.md), Gihawi 2023): a database of draft microbial
   genomes, some holding human sequence, with no human genome in it.
2. **Vectors and adapters** (UniVec Core), so that synthetic sequence is named as such.
3. **The organisms that actually reach a human library**, including the ones that are not microbes: other animals
   and plants. In saliva genomes a few percent of the reads that align oddly to the human reference come from plants
   and animals people eat, and one public saliva genome is dominated by a wheat relative ([prior-art.md](prior-art.md),
   Samson 2020). An animal's DNA is also the closest to human of any contaminant's, so it is the likeliest to align
   to the human reference and the least likely to be recognised by a microbe-only database.
4. **Its taxonomy files**, shipped with it.
5. **A size that fits a compute node's memory**, or a clear statement of what the memory-mapped mode costs.

## What the published collections hold

Prebuilt kraken2 collections, from the [index page](https://benlangmead.github.io/aws-indexes/k2) (October 2026
update unless dated otherwise):

| Collection | Holds | Human | Other animals | Plants | Index, GB |
| --- | --- | --- | --- | --- | --- |
| Standard | RefSeq archaea, bacteria, viral, plasmid, human, UniVec Core | yes | no | no | 109 |
| PlusPF | Standard plus RefSeq protozoa and fungi | yes | no | no | 116 |
| PlusPFP | Standard plus RefSeq protozoa, fungi and plant | yes | no | yes | 270 |
| Standard-8, -16 and the capped PlusPF / PlusPFP | the same, capped at 8 or 16 GB | yes | no | as the parent | 7.5 to 15 |
| MinusB | RefSeq archaea, viral, plasmid, human, UniVec Core | yes | no | no | 12 |
| core_nt (2025-10-15) | GenBank, RefSeq, TPA and PDB sequence | yes | yes | yes | 316 |
| GTDB v226 representatives (2025-06-09) | bacteria and archaea | no | no | no | 644 |
| EuPathDB (2023) | eukaryotic pathogen genomes, contaminants removed | no | no | no | 11 |
| **PrackenDB** (`k2_NCBI_reference_20251007`) | every NCBI reference assembly of bacteria, archaea, protists and fungi, one per species, plus human, RefSeq viral and UniVec Core | yes | no | no | archive 352 |

"Other animals" and "plants" were checked in each collection's `inspect.txt`: in Standard, PlusPF and PlusPFP the
whole of Metazoa is *Homo sapiens*. PrackenDB has no inspect file; its row rests on its published description.

Two things follow.

**The only published collection with animals is core_nt, and it is not their genomes.** NCBI's core nucleotide
database is nt without most eukaryotic chromosome sequences: it keeps transcripts and gene-related sequence. It can
name a cow's or a chicken's read that falls in a gene; it is 316 GB of memory; and a k-mer database built from
GenBank at large carries GenBank's mislabelled entries with it ([prior-art.md](prior-art.md), Steinegger 2020).

**PrackenDB is the right base for microbes and the screen in use today.** One reference genome per species keeps
the per-species k-mer counts meaningful, and it holds human and UniVec Core. It holds no animal but human and no
plant. In the screen that motivated this tool it also gave three kinds of wrong label on human sequence, each
recurring at one human place across many samples ([validation.md](validation.md), section 5): a label that comes
from the database and not from any library.

## What is proposed

Two databases, used together, and a recipe for a third.

### 1. PrackenDB, as it is, for stage 1

Pinned by file name and md5. It proposes names; stages 2 to 5 verify them. Its known wrong labels on human sequence
are handled downstream, by the rule that a read human sequence explains is never foreign, and are catalogued by
stage 6.

### 2. A small eukaryote panel, searched by alignment

The gap is animals and plants. A k-mer database of whole mammalian genomes is large: MinusB, which is the human
genome and little else, is a 12 GB index, so each further mammal would add about as much. The proposal is to look for
them the cheap way first:

* **Organelle genomes** (mitochondria; chloroplasts for plants) of the species likely to reach a mouth, a bench or a
  cell culture: the common food animals and plants, pets, laboratory animals. Organelle DNA is many copies per cell
  and a few tens of kilobases per species, so a panel of hundreds of species is megabytes, and a library that holds
  an animal's DNA holds its mitochondrion many times over.
* A hit there is a *name*. Stage 3 then fetches that species' nuclear genome and checks the library against it,
  exactly as for a bacterium.
* For the mouth's own bacteria the Human Oral Microbiome Database lists the taxa and offers their genomes; it is the
  natural source for a mouth-specific panel and for the spike-ins.

The human mitochondrial genome and the nuclear copies of it are in the human set, so that a human mitochondrial
read is never given to another animal's mitochondrion (stage 4's rule). Two cautions from the literature shape this
part: plant and animal genomes are too large to carry as alignment decoys for every sample (Samson 2020), which is
why the nuclear genome is fetched only once a species is named; and apparent mouse and tobacco reads in human data
have turned out to be human-like sequence in those assemblies (Tae 2014), which is why an animal's or a plant's name
needs the same verification as a bacterium's.

This panel is this repository's to build and publish: a manifest of accessions with md5s, fetched by
`interloper db fetch`. **Which species go on it is an open question for review** ([roadmap.md](roadmap.md)).

### 3. A purpose-built kraken2 database: the recipe, not yet the build

If the benchmark shows that PrackenDB plus the panel still misses or mislabels too much, the next step is a database
built for this use with `kraken2-build`: PrackenDB's microbes, the human genome in more than one assembly (the
reference and a telomere-to-telomere assembly), UniVec Core, and the eukaryote panel's nuclear genomes where memory
allows. Every input genome would first be screened for foreign sequence (NCBI's FCS-GX), since a human fragment in a
bacterial assembly is a wrong label for every sample ever screened with it. The recipe will be a manifest and a
command, so that anyone can rebuild it; the build itself waits on the benchmark saying it is needed.

## The human set

Stage 4 compares each read with "human", and what that set holds decides how many reads are left unexplained:

| Part | Why |
| --- | --- |
| The reference the data is aligned to, with alts, decoys and HLA | the released alignments are to it |
| A telomere-to-telomere assembly (T2T-CHM13) | sequence the reference lacks: centromeres, acrocentric arms, segmental duplications |
| Pangenome sequence absent from both (HPRC) | common insertions and haplotypes no single assembly holds |
| The mitochondrial genome | so that it is named human, not by its bacterial ancestry |

A read explained only by the second or third part is human, and is also evidence of where the reference falls
short: it is reported as "human, not in the reference".

## Reference genomes for the panel

Fetched by accession from NCBI Datasets, checked against the md5 NCBI ships, cached under one directory, and listed
with accession and md5 in every output. `--offline` uses the cache alone. Nothing is fetched by name: a species
name is resolved to an accession once, and the accession is what is recorded.

## Memory

kraken2 loads the whole index into memory, or memory-maps it and runs slower. PrackenDB's archive is 352 GB; the
page lists no index size for it, and the other collections' indexes are about 1.3 times their archives. So stage 1 is
a job for a large-memory node, run once per sample on a few million reads. Everything after it is expected to run in
a few gigabytes. Whether a capped collection can stand in as a first pass on small machines is a benchmark question,
not an assumption.

## Sources

* Kraken 2 and Bracken index page: <https://benlangmead.github.io/aws-indexes/k2>
* Kraken 2 downloads page (PrackenDB's description): <https://ccb.jhu.edu/software/kraken2/index.shtml?t=downloads>
* NCBI on core_nt: <https://ncbiinsights.ncbi.nlm.nih.gov/2024/07/18/new-blast-core-nucleotide-database/>
* kraken2 manual: <https://github.com/DerrickWood/kraken2/blob/master/docs/MANUAL.markdown>
