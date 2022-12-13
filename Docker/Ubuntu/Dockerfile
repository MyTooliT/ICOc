FROM ubuntu

# Copy source files
COPY mytoolit /icoc/mytoolit
COPY MANIFEST.in \
     pyproject.toml \
     ReadMe.md \
     /icoc/

# Install required tools
RUN apt-get update && \
    apt-get install -y git python3-pip

# Install current version of pip and Setuptools
RUN python3 -m pip install -U pip setuptools

# Install ICOc
RUN pip3 install /icoc

ENTRYPOINT "/bin/sh"
