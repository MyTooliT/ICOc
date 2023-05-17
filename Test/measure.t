-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Measure Subcommand ----------------------------------------------------

  $ icon measure -t 5 -d 0

  $ runtime=$(icoanalyzer Measurement.hdf5 | 
  >           grep 'Runtime:' | 
  >           sed -E 's/[^0-9]+([0-9]*\.[0-9]+).*/\1/')

Check that runtime is approximately correct

  $ python3 -c "exit(0 if 4.5 < $runtime < 5.1 else 1)"

-- Cleanup ---------------------------------------------------------------------

  $ rm Measurement.hdf5
