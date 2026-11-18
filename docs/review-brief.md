# interloper: the brief for an external review

You are reviewing the design of `interloper` before any of it is built. It is a public, open-source tool for
identifying non-human DNA in human sequencing by positive evidence, aimed first at family studies of DNA taken from
the mouth (saliva, buccal swabs), where anything in one person's library and not in the others looks like a de novo
variant.

Your job is to find what is wrong, what is missing and what has been done before. Praise is of no use here, and
neither is a restatement of our documents. If the design is sound somewhere, say so in one line and move on.

## 0. What to read first

The repository is <https://github.com/jlanej/interloper>. Read these whole before you search for anything:

| File | What it is |
| --- | --- |
| `README.md` | the idea in one page |
| `docs/design.md` | the method: six stages, the read classes, every rule with its starting value |
| `docs/prior-art.md` | the work each idea is taken from, as we understand it |
| `docs/databases.md` | what the published kraken2 collections hold, and what we propose |
| `docs/validation.md` | the litmus set of real reads, the planned spike-ins, the acceptance criteria |
| `docs/roadmap.md` | the milestones and **14 numbered questions for you** |
| `tests/data/litmus/truth_summary.tsv` | the litmus set's result, one row per place and family member |

Each is also at `https://raw.githubusercontent.com/jlanej/interloper/main/<path>`.

**If you cannot open the repository, say so and stop.** Do not review from this brief alone.

For orientation only, the design in four sentences. An organism is called present in a library when a named genome is
covered by the library's reads the way a genome sampled at random is covered. A read is called foreign when that
genome explains it clearly better than any human sequence does, where "human" includes more than one reference. A
candidate variant is called foreign when the reads it rests on are. Everything else is reported as human, ambiguous
or unexplained; a k-mer classifier (kraken2, through our existing `nonhuman-screen`) only proposes names.

## 1. What we need from you, in order of importance

**1. Errors and overclaims in our documents.** Check the factual claims in `prior-art.md` and `databases.md`
against their sources: each one-line summary of a paper, each statement of what a database holds. Check `design.md`
and `validation.md` for claims the cited work does not support, and for places where we credit ourselves with
something already published. We verified titles, authors and DOIs; we are less sure of our one-line readings.

**2. Prior work we missed.** Search these in particular, and anything they lead to:

* a method that decides, for the reads supporting a candidate variant, whether they are non-human (under any name);
* false de novo or false structural-variant calls caused by contamination, in trios or any family design;
* how large studies that sequence saliva or buccal DNA handle non-human reads before calling variants, de novo
  variants above all;
* ancient-DNA and forensic practice for authenticating reads and for competitive mapping against several genomes;
* telling integrated or inherited viral sequence from contamination (endogenous retroviruses, chromosomally
  integrated herpesvirus 6, hepatitis B, papillomavirus), and Epstein-Barr virus in cell lines;
* statistics for "this genome is present" at low depth: breadth against depth, containment with a coverage model,
  distinct k-mers against reads, hypothesis tests of presence;
* identifying human reads with a telomere-to-telomere assembly or a pangenome, and what remains unexplained after;
* what followed the retracted cancer-microbiome analysis: recommended practice for calling microbes in human
  sequencing;
* lists of reagent, water-system and laboratory contaminants since 2014;
* food, pet and other animal or plant DNA in human sequencing data;
* benchmarks of kraken2's false positives and of its confidence and database settings.

**3. The 14 questions in `docs/roadmap.md`.** Answer each by its number: the answer, the evidence, your confidence
(high, medium or low), and - where the literature cannot settle it - the smallest experiment on public data that
would.

**4. Ways the design fails that it does not mention.** Biological and technical: sequence shared between human and
other genomes by descent or transfer; nuclear copies of organelle DNA; reference decoys; low-complexity reads;
control spike-ins; a contaminant with no sequenced relative; a contaminant that is another human's microbes. For
each: how likely, how it would show, and what the design should do.

**5. The databases.** Is "the published one-genome-per-species collection for the screen, plus a small eukaryote
panel found by organelle genomes, plus a recipe for a purpose-built database later" the right plan? What is better,
at what memory and what licence? Which species belong on a panel for mouth-derived DNA, and on what evidence?

**6. Public data to validate on.** We have two contaminated libraries of cell-line DNA and no mouth-derived truth
set. Find public data that could be one, and for each give the accession, the tissue, the design, what independent
truth exists (matched blood, relatives, long reads of the same person), the size, and **the access terms as the
source states them** (open, registered, controlled). Check at least: open-consent personal genome projects that
sequenced saliva; the public saliva genome and the matched blood, saliva and buccal genomes named in
`roadmap.md`, question 12; and published reports of specific contaminated public sequencing runs that could become
further litmus cases, with their run accessions.

**7. The statistics.** Where a rule in `design.md` is a rule of thumb (a genome is present; an event is foreign;
the thresholds 0.88, 0.10 and 0.95; "at least three molecules"), propose something better founded that can still be
explained in a sentence, and say how to calibrate it on public data. Say whether the acceptance numbers in
`validation.md`, section 7, are the right quantities and the right sizes.

**8. Where this stands.** In a paragraph: what, if anything, is new here once the prior work is counted fairly;
which claim a journal referee would attack first; and the three experiments without which the work should not be
believed.

## 2. Rules of evidence

* **Confirm every reference on a primary source** - the PubMed record, the DOI, the journal, the preprint server, the
  tool's own documentation. Give the DOI or URL you confirmed it on. Mark each VERIFIED, PARTLY (say what is not
  confirmed) or NOT VERIFIED. Never cite from memory, and never give a reference you could not open.
* **If a paper we describe says something else, or does not exist as described, say so** and give the closest real
  one.
* **Keep what the literature says apart from what you reason.** Label your own inference as yours.
* **A negative result needs its searches.** "Nothing found" comes with the queries you ran and where.
* **Paraphrase.** No quotation longer than a few words.
* **Date your facts** where they can change: database contents and sizes, software versions, access terms.

## 3. Limits

* **Public data only.** This repository admits nothing from controlled-access or otherwise restricted data, in any
  form (`CONTRIBUTING.md`). You may list a restricted data set and say it is restricted; do not propose it as test
  data, and do not report any number from one.
* **Review this design; do not replace it.** Recommend changes to it, each tied to evidence. If you think the whole
  approach is wrong, say that first, in section 1 of your report, with the reason.
* **What a change must live with:** it runs in a container on a cluster without network access; reads never leave
  the machine; the screen is kraken2 through `nonhuman-screen`; the implementation language is Python; the licence
  is MIT, so say where a database's or a data set's licence constrains its use.
* **No code is wanted.** Formulas, yes.

## 4. What to return

One Markdown document, to be committed as `docs/review-2026-11.md`, with exactly these sections:

1. **Verdict.** Five to ten lines: the most important things first.
2. **Errors and overclaims.** A table: file and section; what it says (a few words); what is right; the source.
3. **Prior work missed.** A table: the work; what it does; which stage or claim of ours it bears on; the reference
   with DOI or URL; its verification status.
4. **The 14 questions.** One subsection each, by number: answer, evidence, confidence, experiment.
5. **Failure modes.** A list, the most damaging first.
6. **Databases.** Recommendations, with memory and licence.
7. **Public data.** A table as section 1, item 6 asks; say which you recommend first and why.
8. **Statistics.** The proposed rules, with formulas and how to calibrate each.
9. **Recommended changes to the design.** Ranked. Each: what to change, why, the evidence, and what it costs.
10. **Where this stands.** The paragraph of section 1, item 8.
11. **Not resolved.** What you could not settle, with what you tried.

Tables over prose wherever the content is a list. No summary of our documents. Length as needed for sections 2 to 9;
nothing else needs more than a paragraph.
