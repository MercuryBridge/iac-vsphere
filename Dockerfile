FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl wget software-properties-common; \
    install -m 0755 -d /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc; \
    chmod a+r /etc/apt/keyrings/docker.asc; \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null; \
    apt-get update; \
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

RUN apt-get update && \
    wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq && \
    yq --version

COPY requirements/requirements.apt .
RUN apt-get update && \
    sed 's/#.*//' requirements.apt | xargs apt-get install -y && \
    apt-get clean all

COPY requirements/requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt && \
    rm -fr /root/.cache/pip/

COPY requirements/requirements.yml .
RUN ansible-galaxy collection install -v -r requirements.yml && \
    ansible-galaxy role install -v -r requirements.yml --ignore-errors
