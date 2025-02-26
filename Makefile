# -- Variables -----------------------------------------------------------------

BOOKDOWN_DIRECTORY := Bookdown
SPHINX_DIRECTORY := Sphinx
SPHINX_INPUT_DIRECTORY := Documentation/API
INDEX_FILE := Documentation/Introduction.md
OUTPUT_NAME := Documentation

PDF_FILE := $(BOOKDOWN_DIRECTORY)/$(OUTPUT_NAME).pdf
EPUB_FILE := $(BOOKDOWN_DIRECTORY)/$(OUTPUT_NAME).epub
HTML_FILE := $(BOOKDOWN_DIRECTORY)/$(OUTPUT_NAME).html

# Note: The pytest plugin `pytest-sphinx` (version 0.6.3) does unfortunately not
# find our API documentation doctests, hence we specify the test files (*.rst)
# manually.
TEST_LOCATIONS := $(SPHINX_INPUT_DIRECTORY)/api.rst icotronic Test

ifeq ($(OS), Windows_NT)
	OPERATING_SYSTEM := windows
	# Disable Prysk Pytest plugin
	export PYTEST_DISABLE_PLUGIN_AUTOLOAD := ""
else
	OS_NAME := $(shell uname -s)
	ifeq ($(OS_NAME), Linux)
		OPERATING_SYSTEM := linux
	else
		OPERATING_SYSTEM := mac
	endif
endif

# -- Rules ---------------------------------------------------------------------

run: check test hardware-test

# =========
# = Tests =
# =========

check:
	flake8
	mypy icotronic
	pylint icotronic

.PHONY: test
test: pytest-test
test-no-hardware: pytest-test-no-hardware

# ----------
# - Pytest -
# ----------

pytest-test:
	pytest $(TEST_LOCATIONS)

pytest-test-no-hardware:
	pytest --ignore-glob='*network.py' \
	       --ignore-glob='*commander.py' \
	       --ignore-glob='*read_data.t' \
	       --ignore-glob='*sth_name.t' \
	       --ignore-glob='*store_data.t' \
	       --ignore-glob='*measure.t' \
	       --ignore='Documentation'

# ------------------
# - Hardware Tests -
# ------------------

hardware-test: run-hardware-test open-test-report-$(OPERATING_SYSTEM)

run-hardware-test:
	test-sth -v
	test-stu -k eeprom -k connection

open-test-report-windows:
	@powershell -c "Invoke-Item (Join-Path $$PWD 'STH Test.pdf')"
	@powershell -c "Invoke-Item (Join-Path $$PWD 'STU Test.pdf')"

open-test-report-mac:
	@open 'STH Test.pdf' 'STU Test.pdf'

open-test-report-linux:
	@if [ -z "$(DISPLAY)" ]; \
	then \
	  printf "Please check the files “STH Test.pdf” and “STU Test.pdf”\n"; \
	else \
	  xdg-open 'STH Test.pdf'; \
	  xdg-open 'STU Test.pdf'; \
	fi

# =================
# = Documentation =
# =================

# ------------
# - Bookdown -
# ------------

doc: init $(EPUB_FILE) $(HTML_FILE) $(PDF_FILE) cleanup

# Copy pictures to repository root and create diagrams
init:
	Rscript -e "dir.create('Pictures')"
	Rscript -e "file.copy('Documentation/Pictures', '.', recursive=T)"

# Remove pictures from repository root
cleanup:
	Rscript -e "unlink('Pictures', recursive = TRUE)"

epub: init $(EPUB_FILE) cleanup
html: init $(HTML_FILE) cleanup
pdf: init $(PDF_FILE) cleanup

# Generate EPUB document
$(EPUB_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::epub_book')"

# Generate (GitBook) HTML document
$(HTML_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::gitbook')"
	Rscript -e "file.rename('$(HTML_FILE)', '$(BOOKDOWN_DIRECTORY)/index.html')"

# Generate PDF
$(PDF_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::pdf_book')"

clean: cleanup
	Rscript -e "unlink('$(BOOKDOWN_DIRECTORY)', recursive = TRUE)"
	Rscript -e "unlink('$(SPHINX_DIRECTORY)', recursive = TRUE)"

# -------
# - API -
# -------

.PHONY: doc-api
doc-api:
	sphinx-build -M html $(SPHINX_INPUT_DIRECTORY) $(SPHINX_DIRECTORY)
