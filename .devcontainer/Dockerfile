FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3 AS kcov-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Build-only dependencies do not enter the development image.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential=12.10ubuntu1 \
        ca-certificates=20260601~24.04.1 \
        cmake=3.28.3-1build7 \
        curl=8.5.0-2ubuntu10.15 \
        libcurl4-openssl-dev=8.5.0-2ubuntu10.15 \
        libdw-dev=0.190-1.1ubuntu0.1 \
        libssl-dev=3.0.13-0ubuntu3.16 \
        python3-minimal=3.12.3-0ubuntu2.1 \
    && rm -rf /var/lib/apt/lists/*

ARG KCOV_VERSION=43
RUN curl -fsSL "https://codeload.github.com/SimonKagstrom/kcov/tar.gz/refs/tags/v${KCOV_VERSION}" -o /tmp/kcov.tar.gz \
    && echo "4cbba86af11f72de0c7514e09d59c7927ed25df7cebdad087f6d3623213b95bf  /tmp/kcov.tar.gz" | sha256sum --check --strict \
    && tar -xzf /tmp/kcov.tar.gz -C /tmp \
    && cmake -S "/tmp/kcov-${KCOV_VERSION}" -B /tmp/kcov-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
    && cmake --build /tmp/kcov-build --parallel 2 \
    && cmake --install /tmp/kcov-build

FROM kcov-builder AS python-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libbz2-dev=1.0.8-5.1ubuntu0.1 \
        libffi-dev=3.4.6-1build1 \
        liblzma-dev=5.6.1+really5.4.5-1ubuntu0.3 \
        libsqlite3-dev=3.45.1-1ubuntu2.8 \
        xz-utils=5.6.1+really5.4.5-1ubuntu0.3 \
        zlib1g-dev=1:1.3.dfsg-3.1ubuntu2.2 \
    && rm -rf /var/lib/apt/lists/*

ARG PYTHON_VERSION=3.13.16
RUN curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz" -o /tmp/python.tar.xz \
    && echo "f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d  /tmp/python.tar.xz" | sha256sum --check --strict \
    && tar -xJf /tmp/python.tar.xz -C /tmp

WORKDIR /tmp/Python-${PYTHON_VERSION}
RUN ./configure --prefix=/opt/python --with-ensurepip=install \
    && make --jobs=2 \
    && make install \
    && install -Dm644 LICENSE /opt/python/share/licenses/CPython/LICENSE

FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Explicit versions: update in a PR, then rebuild the image.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates=20260601~24.04.1 \
        curl=8.5.0-2ubuntu10.15 \
        git=1:2.43.0-1ubuntu7.3 \
        libdw1t64=0.190-1.1ubuntu0.1 \
        libbz2-1.0=1.0.8-5.1ubuntu0.1 \
        libffi8=3.4.6-1build1 \
        liblzma5=5.6.1+really5.4.5-1ubuntu0.3 \
        libsqlite3-0=3.45.1-1ubuntu2.8 \
        libssl3t64=3.0.13-0ubuntu3.16 \
        zlib1g=1:1.3.dfsg-3.1ubuntu2.2 \
        ripgrep=14.1.0-1 \
        xz-utils=5.6.1+really5.4.5-1ubuntu0.3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-builder /opt/python /opt/python
COPY python/requirements.lock /opt/python-tools/requirements.lock
RUN /opt/python/bin/python3.13 -m venv /opt/python-tools \
    && /opt/python-tools/bin/python -m pip --isolated install --no-cache-dir \
        --require-hashes --only-binary=:all: --index-url https://pypi.org/simple \
        --requirement /opt/python-tools/requirements.lock \
    && /opt/python-tools/bin/python -m pip check

ENV PATH="/opt/python-tools/bin:/opt/python/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=kcov-builder /usr/local/bin/kcov /usr/local/bin/kcov
COPY --from=kcov-builder /usr/local/share/doc/kcov /usr/local/share/doc/kcov

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

ARG GITLEAKS_VERSION=8.30.1
ARG HADOLINT_VERSION=2.15.1
RUN case "$(dpkg --print-architecture)" in \
        amd64) leaks_arch=x64; leaks_sha=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb; lint_arch=x86_64; lint_sha=c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507 ;; \
        arm64) leaks_arch=arm64; leaks_sha=e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080; lint_arch=arm64; lint_sha=f6198ef8090f404dbb771abfee086eb8c48ac177f30da7fd3510aca35b344b5d ;; \
        *) echo "Unsupported quality-tool architecture" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${leaks_arch}.tar.gz" -o /tmp/gitleaks.tar.gz \
    && echo "${leaks_sha}  /tmp/gitleaks.tar.gz" | sha256sum --check --strict \
    && tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks \
    && curl -fsSL "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-linux-${lint_arch}" -o /usr/local/bin/hadolint \
    && echo "${lint_sha}  /usr/local/bin/hadolint" | sha256sum --check --strict \
    && chmod 0755 /usr/local/bin/gitleaks /usr/local/bin/hadolint \
    && rm /tmp/gitleaks.tar.gz

COPY quality/package.json quality/package-lock.json /opt/quality/
RUN npm ci --prefix /opt/quality --omit=dev --ignore-scripts --no-audit --no-fund \
    && ln -s /opt/quality/node_modules/.bin/eslint /usr/local/bin/eslint \
    && npm cache clean --force

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
USER 1000:1000
WORKDIR /workspaces/soulkiller
CMD ["sleep", "infinity"]
