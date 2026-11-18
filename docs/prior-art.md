# Prior work, and what interloper takes from it

None of the pieces of interloper is new. Classifying reads by k-mers, telling a present genome from a spurious hit,
subtracting the host and aligning the rest, choosing between two genomes by comparing alignments: each is published
and in use. This page says which idea comes from where, and what is different here.

**How the citations were checked.** Every paper below was confirmed on 2026-11-18 against its PubMed record and its
DOI's Crossref record (JOSS and bioRxiv items against those sites). The one-line summaries paraphrase the abstracts.
Tool facts were read from the tools' own manuals and release pages. A paper that could not be confirmed is not
listed.

## 1. Labelling reads by k-mers: the screen

| Work | Idea taken |
| --- | --- |
| Kraken 2 (Wood 2019) | exact k-mer matches to a taxonomy, lowest common ancestor per read: fast enough to label millions of reads against every reference genome. It is the screen. |
| Bracken (Lu 2017) | re-estimating abundance from the read labels and the genomes' own k-mer content |
| Centrifuge (Kim 2016) | the same job on a compressed index small enough for very large sequence collections |
| The Kraken suite protocol (Lu 2022) | a worked protocol that includes pathogen detection in a human clinical sample |

**Different here:** the label is where interloper starts, not what it reports.

## 2. Is the organism there, or is it one locus hit many times?

| Work | Idea taken |
| --- | --- |
| KrakenUniq (Breitwieser 2018) | count the *distinct* k-mers a taxon's reads cover: a real genome gives many, a false positive gives few. kraken2 has carried the same idea since v2.1.0 as `--report-minimizer-data` (marked experimental in its manual). |
| KMCP (Shen 2023) | combine k-mer similarity with coverage over chunks of each genome, stated as a way to lower false positives |
| Mash Screen (Ondov 2019) | how much of each reference genome is *contained* in a read set, with contamination screening as a named use |
| sourmash (Brown 2016; Irber 2024) and its "gather" (Irber 2022, a preprint) | containment between sets of different sizes, and composition as the smallest set of genomes that covers the sample's k-mers |
| MetaPhlAn 4 (Blanco-Míguez 2023) | presence by clade-specific marker genes |

**Different here:** these profile a sample. interloper uses the same kind of evidence to decide which genomes to
align a library's reads to, and then tests presence by the alignment itself: breadth against the breadth expected
at that depth, identity, pairing, and the share per lane (design, stage 3).

## 3. Microbes in host sequencing: subtract, then align

| Work | Idea taken |
| --- | --- |
| PathSeq (Kostic 2011) and GATK PathSeq (Walker 2018) | subtract the human reads, align what is left to microbial references, score taxa. The closest existing pipeline to stages 1 to 3. |
| DecontaMiner (Sangiovanni 2019) | the reads that failed to map to the host are where unexpected organisms are found |
| FastQ Screen (Wingett 2018) | align a sample of reads to a panel of genomes and report the share hitting each: the model for a small fixed panel |
| DeconSeq (Schmieder 2011), Hostile (Constantinides 2023) | the reverse direction: removing human reads from microbial data, with measured loss on both sides |

**Different here:** these answer "what else is in this sample". interloper carries the answer to the reads behind
each candidate variant, and requires the named genome to be confirmed in the library before any read is assigned to
it.

## 4. One read, two genomes: choose by comparing alignments

| Work | Idea taken |
| --- | --- |
| Disambiguate (Ahdesmäki 2016) | align the same reads to two species and give each pair to the better alignment, or call it ambiguous |
| XenofilteR (Kluin 2018) | the same by edit distance to each reference |
| Xenome (Conway 2012) | the same four-way outcome - host, graft, both, neither - from k-mers of the two references |

These were built for tumour xenografts, human cells grown in a mouse. Stage 4 is this idea with the panel in the
graft's place, and it keeps their honesty: "both" and "neither" are outcomes, here AMBIGUOUS and UNEXPLAINED.

**Different here:** the second genome is not known in advance. It is named from the library and confirmed in it.

## 5. Why a label can be wrong: the databases

| Work | What it shows |
| --- | --- |
| Breitwieser 2019 | 2,250 bacterial and archaeal genomes in RefSeq carry human sequence, mostly repeats in small contigs of draft assemblies |
| Steinegger 2020 (Conterminator) | mislabelled sequence at scale: more than two million entries in GenBank and more than a hundred thousand in RefSeq, in draft and complete genomes alike |
| Kryukov 2016 | 154 of 45,735 public assemblies hold fragments that are human with high confidence |
| Lu 2018 | cleaning draft eukaryotic pathogen genomes of contaminants cuts false positives in classification |
| Astashyn 2024 (FCS-GX) | NCBI's screen for foreign sequence in assemblies, run across GenBank |
| Gihawi 2023 | a published cancer-microbiome analysis assigned millions of human reads to bacteria: the database held draft genomes with human sequence in them and no human genome. The analysed paper has since been retracted. |

This is the body of work behind interloper's first rule: a read that human sequence explains is never foreign,
whatever a classifier calls it. It is also why [databases.md](databases.md) requires the human genome in the
database and proposes screening every input of a purpose-built one.

## 6. Contamination that reaches a library

| Work | What it shows |
| --- | --- |
| Salter 2014 | contaminating DNA is in extraction kits and reagents everywhere, varies by kit and batch, and lists the genera |
| Laurence 2014 | all 57 runs examined from the 1000 Genomes Project held contaminant reads; *Bradyrhizobium* was the commonest genus, and many of the organisms are known from ultrapure water systems |
| Langdon 2014 | *Mycoplasma* reads in 1000 Genomes data: at least 7% of samples appear contaminated |
| Strong 2014 | substantial, probably environmental, bacterial contamination is routine in existing human RNA-seq data |
| Chrisman 2022 | in unmapped and poorly aligned reads of nearly 5,000 people in more than 1,000 families, contamination tracks sequencing plate and sample source, and Y-chromosome sequence missing from the reference is commonly mistaken for bacteria |
| Tan 2023 | after contaminant filtering, no shared blood microbiome in 9,770 healthy people |
| Davis 2018 (decontam) | contaminants identified statistically, by their frequency against DNA concentration and in negative controls |

The litmus set's first organism, *Methylobacterium organophilum* strain WPA_B, was isolated from a spacecraft's
water processor: the same water-system flora these papers describe. Chrisman 2022 is the nearest study in design -
families, unmapped reads, human sequence mistaken for bacteria - and stops at the sample.

## 7. Mouth-derived DNA, and what it does to variant calls

The closest work to this project. It establishes the problem in saliva and buccal samples, the mechanism, and one
remedy.

| Work | What it shows |
| --- | --- |
| **Samson 2020** | In saliva genomes, non-human reads align to the human reference through short identical stretches flanked by soft clips, and change genotype calls. The clusters were first noticed as calls unique to a child and absent from the parents. Most such reads were bacterial; a few percent came from plants and animals people eat. Aligning to a reference with bacterial genomes added (a decoy) cut the atypical alignments by 44% and removed the anomalous calls. Plant and animal genomes were judged too large to add. |
| **An 2025** | Decoys built from an oral genome catalogue extended with metagenome-assembled genomes improve agreement between blood and oral samples beyond isolate genomes alone; 82 regions carrying clinically catalogued variants have close homologs in oral bacteria. |
| **Trost 2019** | Matched blood, saliva and buccal samples of four people: the share of reads aligned and the depth differ from blood's in saliva and buccal samples; false single-nucleotide calls are slightly more frequent in some; copy-number detection is worse where bacterial content is high. One false exonic variant is traced to short segments of bacterial reads. |
| Kumar 2023 | 765 clinical oral genomes (buccal swabs and saliva): more than four in five have over 5% of reads not mapping to human; bacteria are the majority of those reads |
| Yao 2020 | on average about a tenth of saliva reads map to the oral microbiome, against under a thousandth for blood; copy-number calls agree between blood and saliva only three times in four |
| Quinque 2006; Herráez 2008; Rylander-Rudqvist 2006 | non-human DNA is a large and very variable share of saliva and buccal DNA: the human fraction ranges from a tenth to nearly all, and samples low in human DNA genotype poorly |
| Escapa 2018; Chen 2010; Dewhirst 2010 | the Human Oral Microbiome Database: a curated list of the mouth's taxa with reference genomes for most, downloadable |

**Different here, and owed to this work.** Samson 2020 describes the mechanism the litmus set shows (there, anchors
of at most 24 bases; here 30 to 49), saw it as child-only calls, and found food DNA among the reads. Its remedy and
An 2025's act at alignment: every sample is realigned to human plus a fixed decoy, and what the decoy does not hold -
an organism outside the catalogue, a plant, an animal - is not helped. interloper acts after alignment, on the reads
behind each candidate, with genomes named from the library itself, and says "unexplained" where no genome is found.
The two are complementary, and whether one is strictly better is the second question for review.

## 8. Human sequence beyond one reference, and labels on it

| Work | What it shows |
| --- | --- |
| Nurk 2022 (T2T-CHM13) | a gapless human assembly adding nearly 200 Mbp the reference lacks |
| Liao 2023 (HPRC) | 47 phased assemblies adding 119 Mbp of polymorphic sequence relative to the reference |
| Sherman 2019 | reads of 910 people that fail to align to the reference assemble into nearly 300 Mbp of human sequence absent from it |
| Tae 2014 | in 1000 Genomes data, many apparent mouse and tobacco reads are false signals from human-like sequence in those assemblies |
| Lusk 2014 | laboratory contamination can explain the reported presence of food genes in human blood |
| Moustafa 2017; Kowarsky 2017 | large surveys of non-human sequence in blood: most of the non-human viruses found reflect reagent and environmental contamination; much assembled cell-free sequence matches nothing known |

A read is not foreign because one reference build lacks it, and an animal's or a plant's name on a read is as open
to database error as a bacterium's. The human set of stage 4 ([databases.md](databases.md)) rests on the first three;
the last three are why stage 4's "unexplained" exists.

## 9. What was not found

Searches of PubMed and the web on supporting reads, de novo and structural variants, trios, and contamination found:

* **no published method whose purpose is to decide, for the reads supporting a candidate variant, whether they are
  non-human**;
* **no paper whose main result is false structural-variant calls from contamination** in human sequencing;
* **no paper on false de novo calls from contamination in a trio design** - the nearest is the family observation
  inside Samson 2020.

The nearest published work acts on the sample or the whole read set: decoys at alignment (Samson 2020, An 2025); the
effect of DNA source on calls (Trost 2019); a taxonomic read filter before variant calling in bacterial genomes
(Goig 2020); mouse alleles that align to the human reference in patient-derived models (Jo 2019).

The only software found that works per variant is this project's own lineage:
[nonhuman-screen](https://github.com/jlanej/nonhuman-screen), which gives the non-human fraction of the reads
carrying a variant's ALT allele, and [kmer_denovo_filter](https://github.com/jlanej/kmer_denovo_filter), where it
was first written. Whether the search missed something is the first question for review
([roadmap.md](roadmap.md)).

## 10. So what is different

Stated as narrowly as it can be:

1. **The unit is the candidate variant**, and the evidence is the provenance of the reads it rests on - not the
   sample's profile, and not a region's share of labelled reads.
2. **Every "foreign" names a genome that the library is shown to contain**, and every assignment is made against
   the best human explanation of the same read.
3. **The remainder is reported**: ambiguous, unexplained, and labels that recur at one human place across samples.
4. **The design is aimed at family studies**, where anything in one library and not the others is de novo by
   construction - seen in passing by Samson 2020, and here the case the tool is built for - **and at structural
   variants**, where a wrong label hides real events as readily as contamination invents false ones.

## References

Ahdesmäki MJ, et al. Disambiguate: an open-source application for disambiguating two species in next generation
sequencing data from grafted samples. F1000Research 2016;5:2741. doi:10.12688/f1000research.10082.2

An Z, et al. Metagenome-assembled genomes enhance bacterial read decontamination and variant calling in oral
samples. iScience 2025;28(11):113772. doi:10.1016/j.isci.2025.113772

Astashyn A, et al. Rapid and sensitive detection of genome contamination at scale with FCS-GX. Genome Biology
2024;25:60. doi:10.1186/s13059-024-03198-7

Blanco-Míguez A, et al. Extending and improving metagenomic taxonomic profiling with uncharacterized species using
MetaPhlAn 4. Nature Biotechnology 2023;41:1633-1644. doi:10.1038/s41587-023-01688-w

Breitwieser FP, Baker DN, Salzberg SL. KrakenUniq: confident and fast metagenomics classification using unique k-mer
counts. Genome Biology 2018;19:198. doi:10.1186/s13059-018-1568-0

Breitwieser FP, et al. Human contamination in bacterial genomes has created thousands of spurious proteins. Genome
Research 2019;29:954-960. doi:10.1101/gr.245373.118

Brown CT, Irber L. sourmash: a library for MinHash sketching of DNA. Journal of Open Source Software 2016;1(5):27.
doi:10.21105/joss.00027

Byrska-Bishop M, et al. High-coverage whole-genome sequencing of the expanded 1000 Genomes Project cohort including
602 trios. Cell 2022;185:3426-3440.e19. doi:10.1016/j.cell.2022.08.004

Chen T, et al. The Human Oral Microbiome Database: a web accessible resource for investigating oral microbe
taxonomic and genomic information. Database (Oxford) 2010;2010:baq013. doi:10.1093/database/baq013

Chrisman B, et al. The human "contaminome": bacterial, viral, and computational contamination in whole genome
sequences from 1000 families. Scientific Reports 2022;12:9863. doi:10.1038/s41598-022-13269-z

Constantinides B, Hunt M, Crook DW. Hostile: accurate decontamination of microbial host sequences. Bioinformatics
2023;39:btad728. doi:10.1093/bioinformatics/btad728

Conway T, et al. Xenome - a tool for classifying reads from xenograft samples. Bioinformatics 2012;28:i172-i178.
doi:10.1093/bioinformatics/bts236

Davis NM, et al. Simple statistical identification and removal of contaminant sequences in marker-gene and
metagenomics data. Microbiome 2018;6:226. doi:10.1186/s40168-018-0605-2

Dewhirst FE, et al. The human oral microbiome. Journal of Bacteriology 2010;192:5002-5017. doi:10.1128/JB.00542-10

Escapa IF, et al. New insights into human nostril microbiome from the expanded Human Oral Microbiome Database
(eHOMD): a resource for the microbiome of the human aerodigestive tract. mSystems 2018;3(6):e00187-18.
doi:10.1128/mSystems.00187-18

Gihawi A, et al. Major data analysis errors invalidate cancer microbiome findings. mBio 2023;14:e01607-23.
doi:10.1128/mbio.01607-23. (The paper it re-analyses, Poore et al., Nature 2020, was retracted: Nature
2024;631:694, doi:10.1038/s41586-024-07656-x.)

Goig GA, et al. Contaminant DNA in bacterial sequencing experiments is a major source of false genetic variability.
BMC Biology 2020;18:24. doi:10.1186/s12915-020-0748-z

Herráez DL, Stoneking M. High fractions of exogenous DNA in human buccal samples reduce the quality of large-scale
genotyping. Analytical Biochemistry 2008;383:329-331. doi:10.1016/j.ab.2008.08.015

Irber L, et al. Lightweight compositional analysis of metagenomes with FracMinHash and minimum metagenome covers.
bioRxiv 2022. doi:10.1101/2022.01.11.475838 (preprint; no journal version on record).

Irber L, et al. sourmash v4: a multitool to quickly search, compare, and analyze genomic and metagenomic data sets.
Journal of Open Source Software 2024;9(98):6830. doi:10.21105/joss.06830

Jo SY, Kim E, Kim S. Impact of mouse contamination in genomic profiling of patient-derived models and best practice
for robust analysis. Genome Biology 2019;20:231. doi:10.1186/s13059-019-1849-2

Kim D, et al. Centrifuge: rapid and sensitive classification of metagenomic sequences. Genome Research
2016;26:1721-1729. doi:10.1101/gr.210641.116

Kluin RJC, et al. XenofilteR: computational deconvolution of mouse and human reads in tumor xenograft sequence data.
BMC Bioinformatics 2018;19:366. doi:10.1186/s12859-018-2353-5

Kostic AD, et al. PathSeq: software to identify or discover microbes by deep sequencing of human tissue. Nature
Biotechnology 2011;29:393-396. doi:10.1038/nbt.1868

Kowarsky M, et al. Numerous uncharacterized and highly divergent microbes which colonize humans are revealed by
circulating cell-free DNA. PNAS 2017;114:9623-9628. doi:10.1073/pnas.1707009114

Kryukov K, Imanishi T. Human contamination in public genome assemblies. PLoS ONE 2016;11:e0162424.
doi:10.1371/journal.pone.0162424

Kumar A, et al. Microbial contamination and composition of oral samples subjected to clinical whole genome
sequencing. Frontiers in Genetics 2023;14:1081424. doi:10.3389/fgene.2023.1081424

Langdon WB. Mycoplasma contamination in the 1000 Genomes Project. BioData Mining 2014;7:3.
doi:10.1186/1756-0381-7-3

Laurence M, Hatzis C, Brash DE. Common contaminants in next-generation sequencing that hinder discovery of
low-abundance microbes. PLoS ONE 2014;9:e97876. doi:10.1371/journal.pone.0097876

Li H. Minimap2: pairwise alignment for nucleotide sequences. Bioinformatics 2018;34:3094-3100.
doi:10.1093/bioinformatics/bty191

Liao WW, et al. A draft human pangenome reference. Nature 2023;617:312-324. doi:10.1038/s41586-023-05896-x

Lu J, et al. Bracken: estimating species abundance in metagenomics data. PeerJ Computer Science 2017;3:e104.
doi:10.7717/peerj-cs.104

Lu J, Salzberg SL. Removing contaminants from databases of draft genomes. PLoS Computational Biology
2018;14:e1006277. doi:10.1371/journal.pcbi.1006277

Lu J, et al. Metagenome analysis using the Kraken software suite. Nature Protocols 2022;17:2815-2839.
doi:10.1038/s41596-022-00738-y

Lusk RW. Diverse and widespread contamination evident in the unmapped depths of high throughput sequencing data.
PLoS ONE 2014;9:e110808. doi:10.1371/journal.pone.0110808

Moustafa A, et al. The blood DNA virome in 8,000 humans. PLoS Pathogens 2017;13:e1006292.
doi:10.1371/journal.ppat.1006292

Nurk S, et al. The complete sequence of a human genome. Science 2022;376:44-53. doi:10.1126/science.abj6987

Ondov BD, et al. Mash Screen: high-throughput sequence containment estimation for genome discovery. Genome Biology
2019;20:232. doi:10.1186/s13059-019-1841-x

Quinque D, et al. Evaluation of saliva as a source of human DNA for population and association studies. Analytical
Biochemistry 2006;353:272-277. doi:10.1016/j.ab.2006.03.021

Rylander-Rudqvist T, et al. Quality and quantity of saliva DNA obtained from the self-administrated oragene method -
a pilot study on the cohort of Swedish men. Cancer Epidemiology, Biomarkers & Prevention 2006;15:1742-1745.
doi:10.1158/1055-9965.EPI-05-0706

Salter SJ, et al. Reagent and laboratory contamination can critically impact sequence-based microbiome analyses.
BMC Biology 2014;12:87. doi:10.1186/s12915-014-0087-z

Samson CA, et al. Contaminating DNA in human saliva alters the detection of variants from whole genome sequencing.
Scientific Reports 2020;10:19255. doi:10.1038/s41598-020-76022-4

Sangiovanni M, et al. From trash to treasure: detecting unexpected contamination in unmapped NGS data. BMC
Bioinformatics 2019;20(Suppl 4):168. doi:10.1186/s12859-019-2684-x (DecontaMiner)

Schmieder R, Edwards R. Fast identification and removal of sequence contamination from genomic and metagenomic
datasets. PLoS ONE 2011;6:e17288. doi:10.1371/journal.pone.0017288 (DeconSeq)

Sherman RM, et al. Assembly of a pan-genome from deep sequencing of 910 humans of African descent. Nature Genetics
2019;51:30-35. doi:10.1038/s41588-018-0273-y

Shen W, et al. KMCP: accurate metagenomic profiling of both prokaryotic and viral populations by pseudo-mapping.
Bioinformatics 2023;39:btac845. doi:10.1093/bioinformatics/btac845

Steinegger M, Salzberg SL. Terminating contamination: large-scale search identifies more than 2,000,000 contaminated
entries in GenBank. Genome Biology 2020;21:115. doi:10.1186/s13059-020-02023-1 (Conterminator)

Strong MJ, et al. Microbial contamination in next generation sequencing: implications for sequence-based analysis
of clinical samples. PLoS Pathogens 2014;10:e1004437. doi:10.1371/journal.ppat.1004437

Tae H, et al. Large scale comparison of non-human sequences in human sequencing data. Genomics 2014;104:453-458.
doi:10.1016/j.ygeno.2014.08.009

Tan CCS, et al. No evidence for a common blood microbiome based on a population study of 9,770 healthy humans.
Nature Microbiology 2023;8:973-985. doi:10.1038/s41564-023-01350-w

Trost B, et al. Impact of DNA source on genetic variant detection from human whole-genome sequencing data. Journal
of Medical Genetics 2019;56:809-817. doi:10.1136/jmedgenet-2019-106281

Walker MA, et al. GATK PathSeq: a customizable computational tool for the discovery and identification of microbial
sequences in libraries from eukaryotic hosts. Bioinformatics 2018;34:4287-4289. doi:10.1093/bioinformatics/bty501

Yao RA, et al. Quality of whole genome sequencing from blood versus saliva derived DNA in cardiac patients. BMC
Medical Genomics 2020;13:11. doi:10.1186/s12920-020-0664-7

Wingett SW, Andrews S. FastQ Screen: a tool for multi-genome mapping and quality control. F1000Research
2018;7:1338. doi:10.12688/f1000research.15931.2

Wood DE, Lu J, Langmead B. Improved metagenomic analysis with Kraken 2. Genome Biology 2019;20:257.
doi:10.1186/s13059-019-1891-0

The Human Oral Microbiome Database: <https://www.homd.org/>.

Tools: kraken2 manual, <https://github.com/DerrickWood/kraken2/blob/master/docs/MANUAL.markdown>; release v2.1.0
(the distinct-minimizer report), <https://github.com/DerrickWood/kraken2/releases/tag/v2.1.0>.
