ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /opt/swarmcore
COPY pyproject.toml /opt/swarmcore/pyproject.toml
COPY src /opt/swarmcore/src
RUN pip install --no-cache-dir --no-deps .

USER 65532:65532
ENTRYPOINT ["swarmcore-repository-verify"]
