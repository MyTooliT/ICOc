$repoPath = Split-Path -parent $MyInvocation.MyCommand.Definition | Split-Path

# Save current location
$oldPath=Get-Location
# Unfortunately the script is currently not location independent
cd $repoPath
# We assume that `python` is in your path
python mwt.py $args
# Restore old working directory
cd $oldPath
