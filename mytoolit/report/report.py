# -- Imports ------------------------------------------------------------------

from functools import partial
from os.path import abspath, join, dirname
from sys import path as module_path
from typing import List

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Flowable, ListFlowable, Paragraph,
                                SimpleDocTemplate, Spacer, Table)
from reportlab.rl_config import defaultPageSize

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from .pdf import PDFImage
from mytoolit.config import settings

# -- Functions ----------------------------------------------------------------


# noinspection PyUnusedLocal
def _first_page(canvas, document, node):
    """Define the style of the first page of the report"""

    canvas.saveState()

    page_width = defaultPageSize[0]
    page_height = defaultPageSize[1]
    logo_width = 370
    logo_height = 75
    logo_offset = 50
    title_offset = logo_offset + logo_height + 20
    date_offset = title_offset + 20

    logo_filepath = join(repository_root, "Documentation", "Pictures",
                         "MyTooliT.pdf")
    PDFImage(logo_filepath, logo_width,
             logo_height).drawOn(canvas, (page_width - logo_width) / 2,
                                 page_height - logo_offset - logo_height)

    style = getSampleStyleSheet()

    center_width = page_width / 2

    heading1 = style['Heading1']
    canvas.setFont(heading1.fontName, heading1.fontSize)
    canvas.drawCentredString(center_width, page_height - title_offset,
                             f"{node} Test Report")

    canvas.restoreState()


# -- Class --------------------------------------------------------------------


class Report:
    """Generate test reports using ReportLab"""

    story: List[Flowable]  # Improve happiness of PyCharm type checker

    def __init__(self, node):
        """Initialize the report

        Arguments
        ---------

        node:
            A text that specifies the node (either STU or STH) for which a
            report should be generated
        """

        filepath = join(repository_root, 'Report.pdf')

        self.node = node
        self.document = SimpleDocTemplate(
            filepath,
            author='MyTooliT',
            title='Test Report',
            subject='{} Test'.format('Sensory Tool Holder' if node ==
                                     'STH' else 'Stationary Transceiver Unit'))
        self.story = [Spacer(1, 3 * cm)]
        self.styles = getSampleStyleSheet()

        self.general = []
        self.attributes = []
        self.tests = []

    def __add_header(self, text):
        """Add a header at the current position in the document

        Parameters
        ----------

        text:
            The text of the heading
        """

        self.story.append(Spacer(1, 0.2 * cm))
        self.story.append(Paragraph(text, style=self.styles['Heading2']))
        self.story.append(Spacer(1, 0.5 * cm))

    def __add_table(self, data):
        """Add a table at the current position in the document

        Parameters
        ----------

        data:
            The data that should be stored in the table
        """

        table = Table(data)
        table.hAlign = 'LEFT'
        self.story.append(table)

    def add_attribute(self, name, value, sth_attribute=True):
        """Add information about an attribute to the report

        Parameters
        ----------

        name:
            The name of the attribute
        value:
            The value of the attribute
        sth_attribute
            Specifies if the specified name and value stores STH specific data
            or general data
        """

        table = self.attributes if sth_attribute else self.general
        table.append([name, value])

    def add_test_result(self, description, result):
        """Add information about a single test result to the report

        Parameters
        ----------

        description:
            A textual description of the test
        result:
            The unit test result of the test
        """

        test = result.last_test

        result_text = ("<font color='red'>Error</font>" if test.error() else
                       ("<font color='orange'>Failure</font>" if
                        test.failure() else "<font color='green'>Ok</font>"))

        result_text = f"{description}: <b>{result_text}</b>"
        if test.message:
            result_text += f"<br/><br/><b>{test.message}</b><br/><br/>"
        paragraph_result = Paragraph(result_text, style=self.styles['Normal'])
        self.tests.append(paragraph_result)

    def build(self):
        """Store the PDF report"""

        self.__add_header("General")
        self.__add_table(self.general)

        if len(self.attributes) > 0:
            self.__add_header("Attributes")
            self.__add_table(self.attributes)

        self.__add_header("Test Results")
        tests = ListFlowable(self.tests, bulletType='bullet')
        self.story.append(tests)

        first_page = partial(_first_page, node=self.node)
        self.document.build(self.story, onFirstPage=first_page)
