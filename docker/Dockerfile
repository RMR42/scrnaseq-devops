FROM mambaorg/micromamba:2.9.0

LABEL org.opencontainers.image.source="https://github.com/RMR42/scrnaseq-devops"

WORKDIR /app

ENV NUMBA_CACHE_DIR=/tmp/numba_cache

COPY --chown=$MAMBA_USER:$MAMBA_USER docker/environment.yml /tmp/environment.yml

RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER analysis/ ./analysis/

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python", "-m", "analysis.pipeline"]