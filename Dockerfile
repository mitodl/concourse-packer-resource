FROM python:3.13-alpine@sha256:f7a0d041be64b14d19c642fa6b8a9990d1af4921e6dd1dbe7821cbfab52dc0d1
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/resource
CMD ["/bin/sh"]
ARG PACKER_VERSION=1.13.1

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
