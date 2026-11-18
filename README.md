# interloper

**Positive identification of non-human DNA in human sequencing.**

A human sequencing library is not only human: bacteria from the mouth or the bench, a reagent's contaminants, a
control spike-in. Most of that DNA never aligns to the human genome. The part that does becomes false variants, and
because it is in one library and not the others, they look private to the sample - *de novo*, in a family.

The usual remedy is to label reads with a k-mer classifier and flag whatever looks non-human. A label is not a
proof: it is wrong in both directions often enough to hide real variants behind human sequence with a bacterium's
name. interloper asks for positive evidence instead.

| | The claim | What it takes |
| --- | --- | --- |
| **Organism** | "this organism's DNA is in this library" | a named genome, and the library's reads covering it as a genome is covered |
| **Read** | "this read is that organism's" | it aligns to the named genome clearly better than to any human sequence |
| **Event** | "this candidate variant is that organism's reads" | the reads the candidate rests on are that organism's |

Everything else is reported as what it is: human, ambiguous, or unexplained.

## Status: groundwork

The method is designed and not yet built. What exists today:

* **The design**, with every rule and its starting value: [docs/design.md](docs/design.md).
* **The prior work** it takes its ideas from, each citation checked: [docs/prior-art.md](docs/prior-art.md).
* **A survey of kraken2 databases** and what is proposed: [docs/databases.md](docs/databases.md).
* **The validation plan**, with acceptance criteria fixed in advance: [docs/validation.md](docs/validation.md).
* **A litmus set of real reads** (`tests/data/`): two 1000 Genomes children whose library holds a bacterium, their
  parents, and the bacteria's genomes, cut from public files by a script anyone can run again.
* **A container** with kraken2, minimap2, samtools and nonhuman-screen, built and published by CI.
* **The roadmap and the questions open for review**: [docs/roadmap.md](docs/roadmap.md).

## The litmus set in one paragraph

HG01376's library is half *Methylobacterium organophilum*; NA18521's is a quarter *Staphylococcus epidermidis*. A
few of each bacterium's reads carry 30 to 49 bases that match a human gene, were placed there with the rest clipped
and the mate unmapped, and were reported as candidate de novo insertions at nine places. Aligned to the two genomes,
96 of the children's read pairs at those places are the bacterium's, end to end; of the parents' 11,472 read ends at
the same places, none is. CI runs that check on the reads on every push.

## Try it

```bash
docker run --rm ghcr.io/jlanej/interloper:latest doctor
```

```
kraken2          Kraken version 2.17.1  (/usr/local/bin/kraken2)
minimap2         2.30-r1287  (/usr/local/bin/minimap2)
samtools         samtools 1.21  (/usr/bin/samtools)
nonhuman-screen  0.1.8
ok
```

On a cluster:

```bash
apptainer build interloper.sif docker://ghcr.io/jlanej/interloper:latest
apptainer run interloper.sif doctor
```

From source:

```bash
pip install -e '.[test]'
pytest -q                             # the litmus rule runs again if minimap2 is installed
python tests/data/check_manifest.py   # the litmus files are the ones the manifest names
```

## Where it sits

* [nonhuman-screen](https://github.com/jlanej/nonhuman-screen) runs kraken2 and reduces its labels to a non-human
  fraction. interloper builds on it: the screen proposes names, interloper verifies them.
* [kmer_denovo_filter](https://github.com/jlanej/kmer_denovo_filter) finds de novo variants by k-mers and is the
  first caller interloper is meant to serve ([docs/integration.md](docs/integration.md)).

## Data

The litmus reads are from the 1000 Genomes Project's high-coverage sequencing (Byrska-Bishop et al., Cell 2022),
which is public. The genomes are NCBI RefSeq assemblies. No controlled-access data is in this repository, and none
is used to set any threshold.

## License

MIT. See [LICENSE](LICENSE).
