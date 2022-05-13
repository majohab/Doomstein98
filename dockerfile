FROM python:3.10-alpine3.15

ENV PATH="/scripts:${PATH}"

# Copy pipfile
COPY ./Pipfile /Pipfile

# Install dependencies
RUN apk update && apk upgrade
RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers libffi-dev libressl-dev g++ openssl ca-certificates ssmtp
RUN apk add --update tk
RUN pip install pipenv
RUN pipenv install
RUN pipenv install --system

# Copy app
RUN mkdir /DOOMSTEIN98
COPY ./App /DOOMSTEIN98
WORKDIR /DOOMSTEIN98

# Copy scripts
COPY ./scripts /scripts
RUN chmod +x /scripts/*
RUN dos2unix /scripts/entrypoint.sh
# Last line: Shell can't find the file with its old format

# Add static volume
RUN mkdir -p /vol/web/static

# Add www-data user
RUN set -x ; \
    addgroup -g 82 -S www-data ; \
    adduser -u 82 -D -S -G www-data www-data && exit 0 ; exit 1

# Restrict permissions
RUN chown -R www-data:www-data /vol
RUN chmod -R 755 /vol/web
RUN chown -R www-data:www-data /DOOMSTEIN98

# Switch to user
USER www-data

ENTRYPOINT ["/scripts/entrypoint.sh"]
