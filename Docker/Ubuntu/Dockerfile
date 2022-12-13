FROM ubuntu

# Copy source files
COPY mytoolit /icoc/mytoolit
COPY MANIFEST.in \
     pyproject.toml \
     ReadMe.md \
     /icoc/

# Install required tools
RUN apt-get update && \
    apt-get install -y git python3-venv

# Activate virtual environment
# Source: https://pythonspeed.com/articles/activate-virtualenv-dockerfile
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin":"$PATH"

# Install ICOc
RUN pip3 install /icoc

ENTRYPOINT "/bin/bash"
