FROM ubuntu

# Copy source files
COPY mytoolit /icoc/mytoolit
COPY MANIFEST.in \
     pyproject.toml \
     ReadMe.md \
     /icoc/

# Install required tools
RUN apt-get update && \
    apt-get install -y \
      git \
      python3-numpy \
      python3-pip

# Install ICOc
RUN pip install /icoc

ENTRYPOINT "/bin/sh"
