# Version 1.0.10

## Checks

- We also check the code base with the static type checker [Mypy](https://mypy.readthedocs.io)

## Scripts

- We added a script that removes log and PDF files from the repository root. For more information please take a look at the section “Remove Log and PDF Files” of the [script documentation](../Scripts.md).

## Internal

### Message

- Add method `identifier` to receive an identifier object for the current message

### Network (New)

- Add method (`reset_node`) to reset a node in the network
- Implement context manager interface (`with … as`)
