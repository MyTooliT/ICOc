# -- Variables -----------------------------------------------------------------

OUTPUT_DIRECTORY := Bookdown
INDEX_FILE := Documentation/Introduction.md
OUTPUT_NAME := Documentation

PDF_FILE := $(OUTPUT_DIRECTORY)/$(OUTPUT_NAME).pdf
EPUB_FILE := $(OUTPUT_DIRECTORY)/$(OUTPUT_NAME).epub
HTML_FILE := $(OUTPUT_DIRECTORY)/$(OUTPUT_NAME).html

# -- Rules ---------------------------------------------------------------------

# =========
# = Tests =
# =========

check:
	flake8
	mypy mytoolit

test:
	pytest -v

test-python-can:
	pytest --ignore-glob='*cli.py' --ignore-glob='*ui.py'

test-win-no-hardware:
	pytest --ignore-glob='*network.py' --ignore-glob='*commander.py'

test-python-can-no-hardware:
	pytest \
	  --ignore-glob='*network.py' \
	  --ignore-glob='*commander.py' \
	  --ignore-glob='*cli.py' \
	  --ignore-glob='*ui.py'

run-hardware-tests:
	test-sth -v
	test-stu -k eeprom -k connection

run-hardware-tests-windows: run-hardware-tests
	Invoke-Item 'STH Test.pdf'
	Invoke-Item 'STU Test.pdf'

run-hardware-tests-mac: run-hardware-tests
	open 'STH Test.pdf' 'STU Test.pdf'

# =================
# = Documentation =
# =================

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
	Rscript -e "file.rename('$(HTML_FILE)', '$(OUTPUT_DIRECTORY)/index.html')"

# Generate PDF
$(PDF_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::pdf_book')"

clean: cleanup
	Rscript -e "unlink('$(OUTPUT_DIRECTORY)', recursive = TRUE)"
