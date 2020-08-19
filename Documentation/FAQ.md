# Frequently Asked Questions

## Why Does the Git Staging Area Show Uncommitted Files?

You might wonder why the staging area of this project shows certain uncommitted files (e.g. `.pyc` )that are not part of the repository [`.gitignore`](../.gitignore) file. This is the case, since we assume that you use a [global gitignore file](https://stackoverflow.com/questions/7335420/global-git-ignore) that already contains pattern for these common files. For more information, please take a look [here](https://mytoolit.bitrix24.de/workgroups/group/40/wiki/Git/).

## How Can I Fix Execution Policy Errors?

Depending on your current computer settings, your Terminal application might not execute the scripts contained in the [`Scripts`](../Scripts) directory, but instead show an error about the current execution policy.

One option to fix this issue is to set the execution policy to `RemoteSigned` using the following command:

```sh
Set-ExecutionPolicy RemoteSigned
```
