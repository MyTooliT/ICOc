# -- Imports ------------------------------------------------------------------

from importlib import resources
from functools import partial
from pathlib import Path
from typing import List

from reportlab.lib.units import cm
from reportlab.platypus import (Flowable, ListFlowable, Paragraph,
                                SimpleDocTemplate, Spacer, Table)
from reportlab.rl_config import defaultPageSize

from .pdf import PDFImage
from .style import getStyleSheet
from .checkbox import Checkbox

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

    with resources.path("mytoolit.report", "MyTooliT.pdf") as logo_filepath:
        PDFImage(logo_filepath, logo_width,
                 logo_height).drawOn(canvas, (page_width - logo_width) / 2,
                                     page_height - logo_offset - logo_height)

    style = getStyleSheet()

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

        self.node = node
        self.document = SimpleDocTemplate(
            str(Path(__file__).parent.parent.parent / f"{node} Test.pdf"),
            author='MyTooliT',
            title='Test Report',
            subject='{} Test'.format('Sensory Tool Holder' if node ==
                                     'STH' else 'Stationary Transceiver Unit'))
        self.story = [Spacer(1, 3 * cm)]
        self.styles = getStyleSheet()

        self.general = []
        self.attributes = []
        self.tests = []
        self.checks = []

    def __add_header(self, text, subheader=False):
        """Add a header at the current position in the document

        Parameters
        ----------

        text:
            The text of the heading

        subheader:
            Specifies if the header should be a regular header or a (smaller)
            subheader

        """

        header_level = 3 if subheader else 2
        self.story.append(
            Paragraph(text, style=self.styles[f'Heading{header_level}']))

    def __add_table(self, data, column_widths=None):
        """Add a table at the current position in the document

        Parameters
        ----------

        data:
            The data that should be stored in the table

        column_widths:
            The width of each column of the table

        """

        table = Table(data, colWidths=column_widths)
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
            test.message = f"{test.message}".replace("\n", "<br/>")
            result_text += f"<br/><br/><b>{test.message}</b><br/><br/>"
        paragraph_result = Paragraph(result_text, style=self.styles['Normal'])
        self.tests.append(paragraph_result)

    def add_checkbox_item(self, text: str, tooltip=None) -> None:
        """Add a checkbox item to the report

        Parameters
        ----------

        text:
            The text that should be added before the checkbox item in the
            PDF report

        tooltip:
            The tooltip for the checkbox; If you do not specify a tooltip, then
            `text` will also be used for the tooltip.

        """

        self.checks.append((text, Checkbox(text, tooltip)))

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

        if len(self.checks) > 0:
            self.__add_header("Manual Checks")
            # Somehow the text columns of a table will contain a lot of
            # trailing whitespace, if some (other) cells contain non-textual
            # data. We work around that by specifying the size of the first
            # column manually.
            self.__add_table(self.checks, column_widths=[5.2 * cm, None])

        first_page = partial(_first_page, node=self.node)
        self.document.build(self.story, onFirstPage=first_page)
