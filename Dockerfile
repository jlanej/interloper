# interloper - container image for HPC (Docker build -> Apptainer/Singularity run).
#
#   docker build -t interloper .
#   docker run --rm interloper doctor
#
# On HPC via Apptainer:
#   apptainer build interloper.sif docker://ghcr.io/jlanej/interloper:latest
#   apptainer run interloper.sif doctor
#
# The image holds the tools the method shells out to. Databases and reference genomes are NOT in it: they are large,
# and they are fetched and pinned as docs/databases.md describes.
FROM python:3.12-slim

LABEL org.opencontainers.image.title="interloper" \
      org.opencontainers.image.description="Positive identification of non-human DNA in human sequencing: screen the reads, name the genome, verify by alignment" \
      org.opencontainers.image.licenses="MIT"

# kraken2: the release nonhuman-screen is developed and tested against.
# minimap2: the release the litmus truth was derived with (tests/data/make_litmus.py, TRUTH_MINIMAP2).
ARG KRAKEN2_VERSION=v2.17.1
ARG MINIMAP2_VERSION=v2.30

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential git perl zlib1g-dev wget ca-certificates samtools \
    && git clone --depth 1 --branch "${KRAKEN2_VERSION}" https://github.com/DerrickWood/kraken2.git /tmp/kraken2 \
    && /tmp/kraken2/install_kraken2.sh /usr/local/bin \
    && rm -rf /tmp/kraken2 \
    && git clone --depth 1 --branch "${MINIMAP2_VERSION}" https://github.com/lh3/minimap2.git /tmp/minimap2 \
    && if [ "$(uname -m)" = "aarch64" ]; then make -C /tmp/minimap2 arm_neon=1 aarch64=1; else make -C /tmp/minimap2; fi \
    && cp /tmp/minimap2/minimap2 /usr/local/bin/ \
    && rm -rf /tmp/minimap2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/interloper
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir '.[screen]' && python -c "import interloper, nonhuman_screen"

RUN useradd --create-home --uid 1000 runner
USER runner
WORKDIR /data

ENTRYPOINT ["interloper"]
CMD ["--help"]
