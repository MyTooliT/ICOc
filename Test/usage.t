-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Incorrect Usage -------------------------------------------------------

  $ icon measure -1 0 -2 0 -3 0 -d 0
  usage: icon measure [-h] [--log {debug,info,warning,error,critical}]
                      {config,dataloss,list,measure,rename,stu} ...
  icon measure: error: At least one measurement channel has to be enabled
  [2]
