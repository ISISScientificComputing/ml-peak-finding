FROM mantid

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y git \
    && DEBIAN_FRONTEND=noninteractive apt-get clean \
    && git clone https://github.com/ISISScientificComputing/ml-peak-finding.git \
    && git config --global push.default tracking \
    && rm -rf /var/lib/apt/lists/*

