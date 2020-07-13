# -- Imports ------------------------------------------------------------------

from os.path import join
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Flowable, Paragraph, SimpleDocTemplate, Spacer,
                                Table)
from reportlab.rl_config import defaultPageSize
from typing import List

from .pdf import PDFImage

# -- Functions ----------------------------------------------------------------


# noinspection PyUnusedLocal
def _first_page(canvas, document):
    """Define the style of the first page of the report"""

    canvas.saveState()

    page_width = defaultPageSize[0]
    page_height = defaultPageSize[1]
    logo_width = 370
    logo_height = 75
    logo_offset = 50
    title_offset = logo_offset + logo_height + 20

    PDFImage(join('assets', 'MyTooliT.pdf'), logo_width,
             logo_height).drawOn(canvas, (page_width - logo_width) / 2,
                                 page_height - logo_offset - logo_height)

    style = getSampleStyleSheet()['Heading1']
    canvas.setFont(style.fontName, style.fontSize)
    canvas.drawCentredString(page_width / 2, page_height - title_offset,
                             "STH Test Report")

    canvas.restoreState()


# -- Class --------------------------------------------------------------------


class Report:
    """Generate test reports using ReportLab"""

    story: List[Flowable]  # Improve happiness of PyCharm type checker

    def __init__(self):
        """Initialize the report"""

        self.document = SimpleDocTemplate('Report.pdf',
                                          author='MyTooliT',
                                          title='Test Report',
                                          subject='Sensory Tool Holder Test')
        self.story = [Spacer(1, 5 * cm)]
        self.style = getSampleStyleSheet()['Normal']
        self.test_table = []

    def add_test_result(self, description, result):
        """Add information about a single test result to the report"""

        result_text = 'Error' if result.errors else (
            'Failure' if result.failures else 'Ok')

        self.test_table.append([
            description,
            Paragraph(f"<b>{result_text}</b>", style=self.style)
        ])

    def __exit__(self):
        """Store the PDF report"""

        self.story.append(Table(self.test_table))

        self.document.build(self.story, onFirstPage=_first_page)
