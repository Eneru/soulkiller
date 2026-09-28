FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Explicit versions: update in a PR, then rebuild the image.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates=20260601~24.04.1 \
        curl=8.5.0-2ubuntu10.15 \
        git=1:2.43.0-1ubuntu7.3 \
        ripgrep=14.1.0-1 \
        xz-utils=5.6.1+really5.4.5-1ubuntu0.3 \
    && rm -rf /var/lib/apt/lists/*

ARG NODE_VERSION=24.21.0
RUN case "$(dpkg --print-architecture)" in \
        amd64) node_arch=x64; node_sha=fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6 ;; \
        arm64) node_arch=arm64; node_sha=6ad1325edbdb5649c379b75a237147a666c95d4f9ae8d340fef2d1575d289ad2 ;; \
        *) echo "Unsupported Node.js architecture" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" -o /tmp/node.tar.xz \
    && echo "${node_sha}  /tmp/node.tar.xz" | sha256sum --check --strict \
    && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.xz

ENV OPENSPEC_TELEMETRY=0 \
    OPENSPEC_NO_UPDATE_CHECK=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false

COPY tools/package.json tools/package-lock.json /opt/openspec/
RUN npm ci --prefix /opt/openspec --omit=dev --ignore-scripts --no-audit --no-fund \
    && ln -s /opt/openspec/node_modules/.bin/openspec /usr/local/bin/openspec \
    && npm cache clean --force \
    && git config --system --add safe.directory /workspaces/soulkiller \
    && mkdir -p /workspaces/soulkiller \
    && chown ubuntu:ubuntu /workspaces/soulkiller

# The Ubuntu image already provides this non-root user (UID/GID 1000).
USER ubuntu
WORKDIR /workspaces/soulkiller
CMD ["sleep", "infinity"]
