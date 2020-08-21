$repoPath = Split-Path -parent $MyInvocation.MyCommand.Definition | Split-Path

# We assume that `python` is in your path
python "$repoPath/Scripts/convert-mac-base64.py" $args
