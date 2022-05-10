[![Documentation online](https://img.shields.io/badge/Documentation-online-blueviolet)](https://mytoolit.github.io/ICOc/) [![GitHub Workflow Documentation](https://img.shields.io/github/workflow/status/mytoolit/ICOc/Documentation?label=Documentation)](https://mytoolit.github.io/ICOc/) [![GitHub Workflow Tests](https://img.shields.io/github/workflow/status/mytoolit/ICOc/Tests?label=Tests)](https://github.com/MyTooliT/ICOc/actions/workflows/tests.yaml)

# ICOc

This repository contains data collection and test software for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). For more information, please take a look [at the online documentation of ICOc](https://mytoolit.github.io/ICOc/).

## Documentation

While you should be able to read the various Markdown files of the documentation (this file and the files in the directory `Documentation`) separately, we recommend you read the [bookdown](https://bookdown.org) manual instead. We provide a prebuilt version of the documentation [**here**](https://mytoolit.github.io/ICOc/). You can also download the documentation [under the GitHub Actions tab](https://github.com/MyTooliT/ICOc/actions/workflows/documentation.yaml) (just select the latest run and click on the link “ICOc Manual”), and in the [Bitrix24 drive of MyToolit](https://mytoolit.bitrix24.de/docs/path/Documentation%20Repositories/ICOc/).

### Build

If you want to build the documentation yourself, you need the following software:

- [R](https://www.r-project.org),
- [bookdown](https://bookdown.org),
- [make](<https://en.wikipedia.org/wiki/Make_(software)>), and
- (optionally for the PDF version of the manual) the [TinyTeX R package](https://yihui.org/tinytex/).

After you installed the required software you can build the

- HTML (`make html`),
- EPUB (`make epub`), and
- PDF (`make pdf`)

version of the documentation. The output will be stored in the folder `Bookdown` in the root of the repository. If you want to build all versions of the documentation, just use the command

```
make
```

in the repo root.
