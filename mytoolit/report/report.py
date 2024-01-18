"""Support for creating PDF reports

We use these reports as one of the outputs of our hardware tests
"""

# -- Imports ------------------------------------------------------------------

from functools import partial
from importlib.resources import as_file, files
from typing import List

from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
)

from reportlab.rl_config import (  # pylint: disable=no-name-in-module
    defaultPageSize,
)

from mytoolit.report.pdf import PDFImage
from mytoolit.report.style import get_style_sheet
from mytoolit.report.forms import CheckBoxList, KeepTogether, Signature

# -- Functions ----------------------------------------------------------------


# pylint: disable=unused-argument


def _first_page(canvas, document, node):
    """Define the style of the first page of the report"""

    canvas.saveState()

    page_width = defaultPageSize[0]
    page_height = defaultPageSize[1]
    logo_width = 370
    logo_height = 75
    logo_offset = 50
    title_offset = logo_offset + logo_height + 20

    with as_file(files("mytoolit.report") / "MyTooliT.pdf") as logo_filepath:
        PDFImage(logo_filepath, logo_width, logo_height).drawOn(
            canvas,
            (page_width - logo_width) / 2,
            page_height - logo_offset - logo_height,
        )

    style = get_style_sheet()

    center_width = page_width / 2

    heading1 = style["Heading1"]
    canvas.setFont(heading1.fontName, heading1.fontSize)
    canvas.drawCentredString(
        center_width, page_height - title_offset, f"{node} Test Report"
    )

    canvas.restoreState()


# pylint: enable=unused-argument


# -- Class --------------------------------------------------------------------

# pylint: disable=too-many-instance-attributes


class Report:
    """Generate test reports using ReportLab"""

    story: List[Flowable]  # Improve happiness of PyCharm type checker

    def __init__(self, node="Device"):
        """Initialize the report

        Parameters
        ----------

        node:
            A text that specifies the node (e.g. STH) for which a report
            should be generated

        """

        self.node = node
        device_name = {
            "SMH": "Sensory Milling Head",
            "STH": "Sensory Tool Holder",
            "STU": "Stationary Transceiver Unit",
            "Device": "Device",
        }
        self.document = SimpleDocTemplate(
            f"{node} Test.pdf",
            author="MyTooliT",
            title="Test Report",
            subject=f"{device_name[node]} Test",
        )
        self.story = [Spacer(1, 3 * cm)]
        self.styles = get_style_sheet()

        self.general = []
        self.attributes = []
        self.tests = []
        self.checks = []

    def __add_header(self, text):
        """Add a header at the current position in the document

        Parameters
        ----------

        text:
            The text of the heading

        """

        self.story.append(Paragraph(text, style=self.styles["Heading2"]))

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
        table.hAlign = "LEFT"
        self.story.append(table)

    def add_attribute(self, name, value, node_attribute=True):
        """Add information about an attribute to the report

        Parameters
        ----------

        name:
            The name of the attribute

        value:
            The value of the attribute

        sth_attribute

            Specifies if the specified name and value stores node specific data
            or general data

        """

        table = self.attributes if node_attribute else self.general
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

        result_text = (
            "<font color='red'>Error</font>"
            if test.error()
            else (
                "<font color='orange'>Failure</font>"
                if test.failure()
                else "<font color='green'>Ok</font>"
            )
        )

        result_text = f"{description}: <b>{result_text}</b>"
        if test.message:
            test.message = f"{test.message}".replace("\n", "<br/>")
            result_text += f"<br/><br/><b>{test.message}</b><br/><br/>"
        paragraph_result = Paragraph(result_text, style=self.styles["Normal"])
        self.tests.append(paragraph_result)

    def add_checkbox_list(
        self, title: str, boxes: List[str], text_fields: int = 0
    ) -> None:
        """Add a checkbox list to the report

        Parameters
        ----------

        title:
            The title that should be printed before the checkbox list

        boxes:
            A text for each box that should be added to the checkbox list

        text_fields:
            The number of text fields for additional comments that should be
            added at the end of the checklist.

        """

        checkbox_list = CheckBoxList(title, text_fields)

        for box in boxes:
            checkbox_list.add_checkbox_item(box)

        self.checks.append(checkbox_list)

    def build(self):
        """Store the PDF report"""

        if len(self.general) > 0:
            self.__add_header("General")
            self.__add_table(self.general)

        if len(self.attributes) > 0:
            self.__add_header("Attributes")
            self.__add_table(self.attributes)

        if len(self.tests) > 0:
            self.__add_header("Test Results")
            tests = ListFlowable(self.tests, bulletType="bullet")
            self.story.append(tests)

        if len(self.checks) > 0:
            title = Paragraph("Manual Checks", style=self.styles["Heading2"])
            check_lists = [
                checkbox_list.to_flowable() for checkbox_list in self.checks
            ]

            # We try to keep title and the first checklist on the same page
            # Unfortunately, this currently means that all checklists will be
            # added at the same page, even if there would be enough space for
            # some of the checklists on the previous page. We tried to address
            # this by setting the `keepWithNext` attribute in the `Paragraph`
            # and `ParagraphStyle`. Unfortunately this does not change the flow
            # at all, which means the header “Manual Checks” might be added
            # at the end of a page without any following additional content on
            # the same page :(.

            self.story.append(KeepTogether([title, check_lists[0]]))
            self.story.extend(check_lists[1:])

        self.story.append(Signature().to_flowable())

        first_page = partial(_first_page, node=self.node)
        self.document.build(self.story, onFirstPage=first_page)


# pylint: enable=too-many-instance-attributes


# -- Main ---------------------------------------------------------------------

# pylint: disable=import-outside-toplevel


def main():
    """Manual test code for Report"""

    from platform import system
    from subprocess import run

    # Create a example test report
    node = "STH"
    pdf_path = f"{node} Test.pdf"
    report = Report(node)

    report.add_checkbox_list(
        title="Checkbox Title", boxes=["First box", "Second box"]
    )

    report.build()

    # Open the file to check the resulting PDF manually
    if system() == "Windows":
        # fmt: off
        # The function `startfile` is only available on Windows
        # pylint: disable=no-name-in-module
        from os import startfile  # type: ignore
        # pylint: enable=no-name-in-module
        # fmt: on

        startfile(pdf_path)
    else:
        run(
            [f"{'' if system() == 'Darwin' else 'xdg-'}open", pdf_path],
            check=True,
        )


# pylint: enable=import-outside-toplevel


if __name__ == "__main__":
    main()
