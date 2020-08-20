FROM bids/base_fsl

# Install python and nibabel
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install nibabel && \
    apt-get remove -y python3-pip && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV PYTHONPATH=""

COPY run.py /run.py

COPY version /version
