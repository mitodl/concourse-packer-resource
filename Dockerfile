FROM python:3.12-alpine@sha256:a982997504b8ec596f553d78f4de4b961bbdf5254e0177f6e99bb34f4ef16f95
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/resource
CMD ["/bin/sh"]

ARG PACKER_VERSION=1.10.3

RUN apk add --no-cache --update curl openssh && \
    curl "https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip" -o packer.zip && \
    unzip packer.zip -d /bin/ && \
    rm -f packer.zip && \
    packer plugins install github.com/hashicorp/amazon && \
    apk del curl

# copy scripts
COPY bin/* /opt/resource/
# copy library files
COPY lib/* /opt/resource/lib/
