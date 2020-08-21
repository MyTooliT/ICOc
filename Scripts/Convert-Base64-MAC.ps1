$repoPath = Split-Path -parent $MyInvocation.MyCommand.Definition | Split-Path

# We assume that `python` is in your path
python "$repoPath/Scripts/convert-base64-mac.py" $args
