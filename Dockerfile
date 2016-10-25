from centos:7
ENV PATH=$PATH:/usr/local/boutiques/tools
RUN yum update -y &&              \
    yum install -y  gcc           \
                    make          \
                    python-setuptools \
                    ruby          \
                    ruby-devel && \
    mkdir /usr/local/boutiques
COPY tools /usr/local/boutiques/tools/
COPY schema /usr/local/boutiques/schema/

# Install validator and invocation schema
RUN cd /usr/local/boutiques/tools && \
    gem install bundler && \
    bundle install && \
    easy_install pip && \
    pip install jsonschema

