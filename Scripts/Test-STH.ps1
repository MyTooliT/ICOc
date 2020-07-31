$repoPath = Split-Path -parent $MyInvocation.MyCommand.Definition | Split-Path

# We assume that `python` is in your path
python "$repoPath/mytoolit/test/production/sth.py" $args
