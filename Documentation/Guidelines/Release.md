# Release

1. Make sure that **none** of the [tests](Test.md) fail

   - **Note**: Please execute `test-sth`

     1. once with `STH` → `Status` set to `Epoxied`, and
     2. once set to `Bare PCB`

     in the [configuration](../../mytoolit/config/config.yaml). To make sure, that the STU flash test also works, please use both STU test commands described in the section “STU Test” of the [test document](Test.md).

     If you follow the steps above you make sure that the **flash tests work** for both STU and STH, and there are **no unintentional consequences of (not) flashing the chip** before you run the other parts of the test suite.

2. Change the [`__version__`](../../mytoolit/__init__.py) number inside the [`mytoolit`](../../mytoolit) package
3. Push the commit that changes the version number
4. Create a new release [here](https://github.com/MyTooliT/ICOc/releases/new)

   1. Copy the [release notes](../Releases) for the latest version
   2. Paste them into the main text
   3. Decrease the header level of each section by one
   4. Replace links with a permanent version:

      For example instead of

      - `../something.txt` use
      - `https://github.com/MyTooliT/ICOc/blob/REVISION/something.txt`,

      where `REVISION` is the latest version of the master branch (e.g. `8568893f` for version `1.0.5`)

   5. Check that all links work correctly

5. Insert the version number (e.g. `1.0.5`) into the tag field
6. For the release title use “Version VERSION”, where `VERSION` specifies the version number (e.g. “Version 1.0.5”)
7. Click on “Publish Release”
