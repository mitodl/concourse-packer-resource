FROM python:3.11-alpine@sha256:c0bd92cd77326da7f240843fa3aaf7947404d7a03285719d1aa5d5ee35f98d8e
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
