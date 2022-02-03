FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/resource
CMD ["/bin/sh"]

ARG PACKER_VERSION=1.7.10

RUN apk add --no-cache --update curl openssh && \
    curl "https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip" -o packer.zip && \
    unzip packer.zip -d /bin/ && \
    rm -f packer.zip && \
    apk del curl

# copy scripts
COPY bin/* /opt/resource/
# copy library files
COPY lib/* /opt/resource/lib/
