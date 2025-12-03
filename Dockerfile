FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y --no-install-recommends install \
        build-essential \
        git \
        python3 \
        python3-pip \
        vim \
        wget \
        can-utils \
        gdb-multiarch \
        graphviz \
        gcc-multilib \
        g++-multilib \
        can-utils \
        openocd \
        valgrind \
        libncurses5 \
        libncurses5-dev \
        cmake \
        gdb && \
    apt-get -y clean

RUN git config --global --add safe.directory /workspace

RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip install graphviz
RUN pip install reportlab
RUN pip install matplotlib
RUN pip install google-auth==2.40.3
RUN pip install google-auth-oauthlib==1.2.2
RUN pip install google-auth-httplib2==0.2.0
RUN pip install google-api-python-client==2.172.0

RUN wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2 && \
    tar -xf gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2
ENV PATH="/gcc-arm-none-eabi-10.3-2021.10/bin:${PATH}"

# Install Renode
ARG RENODE_VERSION=1.16.0
RUN wget https://github.com/renode/renode/releases/download/v${RENODE_VERSION}/renode_${RENODE_VERSION}_amd64.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends ./renode_${RENODE_VERSION}_amd64.deb python3-dev && \
    rm ./renode_${RENODE_VERSION}_amd64.deb && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install -r /opt/renode/tests/requirements.txt --no-cache-dir

CMD ["/bin/bash"]

WORKDIR /workspace/
