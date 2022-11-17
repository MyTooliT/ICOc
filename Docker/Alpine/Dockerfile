FROM python:alpine

# Copy source files
COPY mytoolit /icoc/mytoolit
COPY MANIFEST.in \
     pyproject.toml \
     ReadMe.md \
     requirements.txt \
     setup.py \
     /icoc/

# Install required tools
RUN apk add git py3-numpy

# ------------------------------------------------------------------------------
# We add and remove the build requirements in the same step below to make the
# image smaller
# ------------------------------------------------------------------------------

# Install specific version of PyTables manually
# See also: https://github.com/PyTables/PyTables/issues/968
RUN apk add blosc-dev bzip2-dev gcc g++ hdf5-dev lzo-dev musl-dev && \
    pip install git+https://github.com/PyTables/PyTables.git@v3.7.0 && \
    apk del gcc g++ musl-dev

# Install requirements
RUN apk add freetype-dev gcc g++ make musl-dev && \
    pip install -r /icoc/requirements.txt && \
    apk del gcc g++ make musl-dev

# Install ICOc
RUN pip install -e /icoc

ENTRYPOINT "/bin/sh"
