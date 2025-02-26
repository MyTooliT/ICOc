-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"
  $ EXAMPLEDIR=../icotronic/examples

-- Check Read Data Example -----------------------------------------------------

Read and store data for five seconds

  $ python $EXAMPLEDIR/store_data.py

The file should approximately store 47620 (9524 · 5) values

  $ h5dump -d acceleration -H test.hdf5 |
  > grep 'DATASPACE  SIMPLE' |
  > sed -E 's/.*DATASPACE  SIMPLE \{ \( ([0-9]+) .*/\1/'
  4[4-9]\d{3} (re)

-- Cleanup ---------------------------------------------------------------------

  $ rm test.hdf5
