# -- Variables -----------------------------------------------------------------

OUTPUT_DIRECTORY := Bookdown
INDEX_FILE := ReadMe.md

PDF_FILE := $(OUTPUT_DIRECTORY)/$(OUTPUT_NAME).pdf
EPUB_FILE := $(OUTPUT_DIRECTORY)/$(OUTPUT_NAME).epub
HTML_FILE := $(OUTPUT_DIRECTORY)/$(OUTPUT_NAME).html

# -- Rules ---------------------------------------------------------------------

# Always regenerate output files
.PHONY: $(EPUB_FILE) $(HTML_FILE) $(PDF_FILE)

all: init $(EPUB_FILE) $(HTML_FILE) $(PDF_FILE) cleanup

# Copy pictures to repository root
init:
	Rscript -e "dir.create('Pictures')"
	Rscript -e "file.copy('Documentation/Pictures', '.', recursive=T)"

# Remove pictures from repository root
cleanup:
	Rscript -e "unlink('Pictures', recursive = TRUE)"

epub: $(EPUB_FILE)
html: $(HTML_FILE)
pdf: $(PDF_FILE)

# Generate EPUB document
$(EPUB_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::epub_book')"

# Generate (GitBook) HTML document
$(HTML_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::gitbook')"

# Generate PDF
$(PDF_FILE):
	Rscript -e "bookdown::render_book('$(INDEX_FILE)', 'bookdown::pdf_book')"

clean: cleanup
	Rscript -e "unlink('$(OUTPUT_DIRECTORY)', recursive = TRUE)"
