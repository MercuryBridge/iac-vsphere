FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PACKER_LATEST_VERSION=1.10.0

RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common; \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -; \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"; \
    apt-cache policy docker-ce; \
    apt-get install -y docker-ce

COPY requirements/requirements.apt .
RUN apt-get update && \
    sed 's/#.*//' requirements.apt | xargs apt-get install -y && \
    apt-get clean all

COPY requirements/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    rm -fr /root/.cache/pip/

COPY requirements/requirements.yaml .
RUN ansible-galaxy collection install -v -r requirements.yaml && \
    ansible-galaxy role install -v -r requirements.yaml --ignore-errors
