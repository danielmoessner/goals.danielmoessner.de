# inspired by: https://snyk.io/blog/best-practices-containerizing-python-docker/
FROM python:3.14-alpine AS alpine-base

# workdir related stuff stuff
WORKDIR /django
ENV PATH="/django/.venv/bin:$PATH"

# install requirements
COPY pyproject.toml /django/pyproject.toml
COPY uv.lock /django/uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --locked --no-dev

# build image
FROM python:3.14-alpine AS build

# least privilege user (with a real home directory for runtime caches)
RUN addgroup -S python \
	&& adduser -S -D -u 999 -G python -h /home/python python \
	&& mkdir -p /home/python \
	&& chown -R python:python /home/python

# Pillow runtime dependencies
RUN apk add --no-cache \
	libjpeg-turbo \
	zlib \
	openjpeg \
	tiff \
	libxcb

# copy files
RUN mkdir /django && chown python:python /django
WORKDIR /django
COPY --from=alpine-base /django/.venv /django/.venv
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

# Ensure containerized management commands (migrate/collectstatic) use the same
# settings as Gunicorn.
ENV DJANGO_SETTINGS_MODULE="config.settings.production"

# change to nonroot user
USER 999

# run
EXPOSE 8080
CMD ["gunicorn", "--chdir", "/django", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--timeout", "240", "--graceful-timeout", "30", "-w", "2", "--access-logfile", "-", "--error-logfile", "-"]
