-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Example Code ----------------------------------------------------------

  $ python ../mytoolit/examples/read_data.py
  Read data values: \[.+\]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[.+\]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[.+\]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[.+\]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[.+\]@\d+\.\d+ #\d{1,3} (re)

  $ python ../mytoolit/examples/sth_name.py
  Connected to sensor device “.+” (re)
