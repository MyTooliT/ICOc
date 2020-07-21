# -- Imports ------------------------------------------------------------------

from os.path import join
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Flowable, ListFlowable, ListItem, Paragraph,
                                SimpleDocTemplate, Spacer, Table)
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
        self.story = [Spacer(1, 3 * cm)]
        self.styles = getSampleStyleSheet()
        self.attributes = []
        self.tests = []

    def add_attribute(self, name, value):
        """Add information about an STH attribute to the report

        Parameters
        ----------

        name:
            The name of the STH attribute
        value:
            The value of the STH attribute
        """

        self.attributes.append([name, value])

    def add_test_result(self, description, result):
        """Add information about a single test result to the report

        Parameters
        ----------

        description:
            A textual description of the test
        result:
            The unit test result of the test
        """

        result_text = ("<font color='orange'>Failure</font>"
                       if result.failure_message else
                       "<font color='green'>Ok</font>")

        normal = self.styles['Normal']
        result_text = f"{description}: <b>{result_text}</b>"
        if result.failure_message:
            result_text += f"<br/><br/>{result.failure_message}<br/><br/>"
        paragraph_result = Paragraph(result_text, style=normal)
        self.tests.append(paragraph_result)

    def __exit__(self):
        """Store the PDF report"""

        def add_header(header):
            self.story.append(Spacer(1, 0.2 * cm))
            self.story.append(Paragraph(header, style=self.styles['Heading2']))
            self.story.append(Spacer(1, 0.5 * cm))

        if len(self.attributes) > 0:
            add_header("Attributes")
            attributes = Table(self.attributes)
            attributes.hAlign = 'LEFT'
            self.story.append(attributes)

        add_header("Test Results")
        tests = ListFlowable(self.tests, bulletType='bullet')
        self.story.append(tests)

        self.document.build(self.story, onFirstPage=_first_page)
