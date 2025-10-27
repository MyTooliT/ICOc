[![GitHub Workflow Documentation](https://img.shields.io/github/actions/workflow/status/mytoolit/ICOc/documentation.yaml?branch=main&label=Documentation)](https://mytoolit.github.io/ICOc/) [![API Documentation](https://img.shields.io/readthedocs/icoc?label=API%20Documentation)](https://icoc.readthedocs.io/en/stable/) [![GitHub Workflow Tests](https://img.shields.io/github/actions/workflow/status/mytoolit/ICOc/tests.yaml?branch=main&label=Tests)](https://github.com/MyTooliT/ICOc/actions/workflows/tests.yaml)

**ICOc is deprecated!**

If you want to:

- **write Python code** that uses the ICOtronic system, please use the [ICOtronic package](https://github.com/MyTooliT/ICOtronic) instead.
- **test ICOtronic hardware**, please use [ICOtest](https://github.com/MyTooliT/ICOtest) instead.
- **collect measurement data** with the ICOtronic system, please use either
  - the command line tool [`icon`](https://mytoolit.github.io/ICOtronic/#data-collection) of the ICOtronic package or
  - the web GUI [ICOdaq](https://git.ift.tuwien.ac.at/ift/icotronic/icodaq).

# ICOc

This repository contains data collection and test software for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). For more information, please take a look [at the online documentation of ICOc](https://mytoolit.github.io/ICOc/).

## Documentation

While you should be able to read the [various Markdown files of the documentation](Documentation) separately, we recommend you read the [bookdown](https://bookdown.org) manual instead. We provide a prebuilt version of the documentation [**here**](https://mytoolit.github.io/ICOc/).

You can also download the documentation [under the GitHub Actions tab](https://github.com/MyTooliT/ICOc/actions/workflows/documentation.yaml) (just select the latest run and click on the link “ICOc Manual”).

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

```sh
make doc
```

in the repo root.
