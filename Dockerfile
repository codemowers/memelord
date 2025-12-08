FROM python:3.12.11-slim

ARG VERSION=0
ENV VERSION=$VERSION
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# update and install software + create necessary dirs
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    ghostscript \
    gcc \
    libc6-dev \
    netcat-openbsd \
    postgresql-client \
    media-types \
    unzip &&\
    mkdir -p /opt/app/docker/ /opt/app/database /opt/app/logs /opt/app/media

# define workdir
WORKDIR /opt/app

COPY entrypoint.sh /opt/app/docker/entrypoint.sh
COPY uwsgi.ini /opt/app/docker/docker_uwsgi.ini
COPY requirements.txt /opt/app/requirements.txt

RUN pip3 install -r requirements.txt \
 && chown -R www-data:www-data /opt/app \
 && chmod -R 750 /opt/app \
 && chmod +x /opt/app/docker/entrypoint.sh


# copy relevant source data
#COPY locale /opt/app/locale
COPY myproject /opt/app/myproject
COPY myapp /opt/app/myapp
COPY manage.py /opt/app/manage.py

# run container as low privileged user
USER www-data

# start uwsgi server
ENTRYPOINT ["/opt/app/docker/entrypoint.sh"]
EXPOSE 8000
STOPSIGNAL SIGTERM
