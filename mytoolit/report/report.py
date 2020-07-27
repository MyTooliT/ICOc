# -- Imports ------------------------------------------------------------------

from datetime import datetime
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
from mytoolit import __version__
from mytoolit.config import settings

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
    date_offset = title_offset + 20

    PDFImage(join(repository_root, join('assets', 'MyTooliT.pdf')), logo_width,
             logo_height).drawOn(canvas, (page_width - logo_width) / 2,
                                 page_height - logo_offset - logo_height)

    style = getSampleStyleSheet()

    center_width = page_width / 2

    heading1 = style['Heading1']
    canvas.setFont(heading1.fontName, heading1.fontSize)
    canvas.drawCentredString(center_width, page_height - title_offset,
                             "STH Test Report")

    canvas.restoreState()


# -- Class --------------------------------------------------------------------


class Report:
    """Generate test reports using ReportLab"""

    story: List[Flowable]  # Improve happiness of PyCharm type checker

    def __init__(self):
        """Initialize the report"""

        filepath = join(repository_root, 'Report.pdf')

        self.document = SimpleDocTemplate(filepath,
                                          author='MyTooliT',
                                          title='Test Report',
                                          subject='Sensory Tool Holder Test')
        self.story = [Spacer(1, 3 * cm)]
        self.styles = getSampleStyleSheet()

        self.general = []
        self.attributes = []
        self.tests = []

        self.__add_gerneral_information()

    def __add_gerneral_information(self):
        """Add a table containing general information to PDF"""

        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime("%H:%M:%S")

        operator = settings.Operator.Name

        attributes = [
            ["ICOc Version", __version__],
            ["Date", date],
            ["Time", time],
            ["Operator", operator],
        ]

        for name, value in attributes:
            self.add_attribute(name, value, sth_attribute=False)

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

        self.document.build(self.story, onFirstPage=_first_page)
