FROM python:3.12-alpine@sha256:ff870bf7c2bb546419aaea570f0a1c28c8103b78743a2b8030e9e97391ddf81b
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/resource
CMD ["/bin/sh"]

ARG PACKER_VERSION=1.11.1

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
