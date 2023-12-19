-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Measure Subcommand ----------------------------------------------------

  $ dataloss=$(icon measure -t 5 -d 0 | grep 'Data Loss' | \
  > sed -E 's/[^0-9]+([0.9]\.[0-9]+)[^0-9]*/\1/')
  $ if [ "$(printf "%s < 0.1\n" "${dataloss}" | bc)" -eq 1 ]; then
  >   printf "Data loss below 10%%\n"
  > else
  >   printf "Data loss equal to or greater than 10%% (%s)\n" "$dataloss"
  > fi
  Data loss below 10%

  $ runtime=$(icoanalyzer Measurement*.hdf5 | 
  >           grep 'Runtime:' | 
  >           sed -E 's/[^0-9]+([0-9]*\.[0-9]+).*/\1/')

Check that runtime is approximately correct

  $ python3 -c "exit(0 if 4.5 < $runtime < 5.1 else 1)"

-- Cleanup ---------------------------------------------------------------------

  $ rm Measurement*.hdf5
