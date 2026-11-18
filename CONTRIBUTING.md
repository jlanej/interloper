# Contributing

## The data rule

**Only publicly available data may appear in this repository, anywhere:** in code, tests, documentation, examples,
issues, pull requests and commit messages.

What that means in practice:

* **Every data set, sample, number and example names its public source** - an accession or a URL - and can be
  regenerated from it by a command in this repository.
* **Nothing from controlled-access or otherwise restricted data, in any form.** Not reads, not variants, not sample
  or participant identifiers, not positions, not per-sample values, and not summary numbers. A count derived from a
  restricted cohort is restricted too.
* **No trace of a private environment:** no local paths, host names, user names or internal project names.
* **Every threshold is set on public data,** by a benchmark that runs here. A rule tuned on data nobody else can see
  is a rule nobody else can check.
* **A finding first seen in private data is shown again on public data,** or by a simulation with a stated seed,
  before it is written down here. If it cannot be shown that way, it does not go in.
* **Tool output pasted into an issue** holds counts, public accessions and verdicts. No read names or positions from
  samples that are not public.

Test data follows the litmus set's pattern ([docs/validation.md](docs/validation.md)): built by a script that reads
only public files, and listed in `tests/data/MANIFEST.tsv` with its size, md5, record count, source and the command
that made it. `tests/test_public_only.py` checks the parts of this rule a machine can check; the rest is on the
author and the reviewer.

## Before a pull request

```bash
pip install -e '.[test]'
pytest -q
python tests/data/check_manifest.py
```

* A command that is listed runs. No stubs: an unbuilt stage is described in [docs/design.md](docs/design.md), not
  half-present in the command line.
* A broken run never looks clean: errors exit non-zero and say what failed.
* An idea taken from published work is credited in [docs/prior-art.md](docs/prior-art.md), with a reference that
  was checked against its PubMed or DOI record.
* A change to a rule or a threshold changes [docs/design.md](docs/design.md) and the benchmark that sets it in the
  same pull request.
