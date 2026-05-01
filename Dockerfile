# inspired by: https://snyk.io/blog/best-practices-containerizing-python-docker/
FROM python:3.14 AS base

# workdir related stuff stuff
WORKDIR /django
ENV PATH="/django/.venv/bin:$PATH"

# install requirements
COPY pyproject.toml /django/pyproject.toml
COPY uv.lock /django/uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --locked --no-dev

# build image
FROM python:3.14-slim AS build

# least privilege user (with a real home directory for runtime caches)
RUN groupadd -g 999 python && useradd -m -d /home/python -u 999 -g python python

# pillow runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libopenjp2-7 libtiff6 libxcb1

# copy files
RUN mkdir /django && chown python:python /django
WORKDIR /django
COPY --from=base /django/.venv /django/.venv
RUN chown -R root:root /django/.venv && chmod -R a+rX /django/.venv
COPY --chown=python:python config /django/config
COPY --chown=python:python apps /django/apps
COPY --chown=python:python static /django/static
COPY --chown=python:python templates /django/templates
COPY --chown=python:python manage.py /django/manage.py

# Runtime state (sqlite DB, secrets, uploads, collected static) is expected
# to be provided via a bind mount at /django/tmp.
RUN mkdir -p /django/tmp && chown python:python /django/tmp

# make commands available
ENV PATH="/django/.venv/bin:$PATH"

# change to nonroot user
USER 999

# run
EXPOSE 8080
CMD ["gunicorn", "--chdir", "/django", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--timeout", "240", "-w", "2"]
