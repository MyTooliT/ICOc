# -- Imports ------------------------------------------------------------------

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer
from reportlab.rl_config import defaultPageSize
from typing import List

# -- Functions ----------------------------------------------------------------


# noinspection PyUnusedLocal
def _first_page(canvas, document):
    """Define the style of the first page of the report"""

    canvas.saveState()

    page_height = defaultPageSize[1]
    page_width = defaultPageSize[0]
    style = getSampleStyleSheet()['Heading1']
    canvas.setFont(style.fontName, style.fontSize)
    canvas.drawCentredString(page_width / 2.0, page_height - 108,
                             "MyTooliT Report")

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
        self.story = [Spacer(1, 3 * cm)]
        self.style = getSampleStyleSheet()['Normal']

    def add_test_result(self, name, result):
        """Add information about a single test result to the report"""

        result_text = 'Error' if result.errors else (
            'Failure' if result.failures else 'Ok')

        self.story.append(
            Paragraph(f"• {name}: <b>{result_text}</b>", self.style))

    def __exit__(self):
        """Store the PDF report"""

        self.document.build(self.story, onFirstPage=_first_page)
