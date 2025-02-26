"""Support code for changing the style of PDF (test reports)"""

# -- Imports ------------------------------------------------------------------

from reportlab.rl_config import (  # pylint: disable=no-name-in-module
    canvas_basefontname,
)
from reportlab.lib.fonts import tt2ps
from reportlab.lib.styles import ListStyle, ParagraphStyle, StyleSheet1
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER

# -- Attributes ---------------------------------------------------------------

base_font = canvas_basefontname
base_font_bold = tt2ps(canvas_basefontname, 1, 0)
base_font_italic = tt2ps(canvas_basefontname, 0, 1)
base_font_bold_italic = tt2ps(canvas_basefontname, 1, 1)

# -- Functions ----------------------------------------------------------------


def get_style_sheet() -> StyleSheet1:
    """Get the default style sheet for PDF reports

    This is more or less a slightly modified version of the
    function `getSampleStyleSheet` shipped with ReportLab.
    """

    stylesheet = StyleSheet1()

    stylesheet.add(
        ParagraphStyle(
            name="Normal", fontName=base_font, fontSize=10, leading=12
        )
    )

    stylesheet.add(
        ParagraphStyle(
            name="BodyText", parent=stylesheet["Normal"], spaceBefore=6
        )
    )
    stylesheet.add(
        ParagraphStyle(
            name="Italic",
            parent=stylesheet["BodyText"],
            fontName=base_font_italic,
        )
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading1",
            parent=stylesheet["Normal"],
            fontName=base_font_bold,
            fontSize=18,
            leading=22,
            spaceAfter=6,
        ),
        alias="h1",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Title",
            parent=stylesheet["Normal"],
            fontName=base_font_bold,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        alias="title",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading2",
            parent=stylesheet["Normal"],
            fontName=base_font_bold,
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
        ),
        alias="h2",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading3",
            parent=stylesheet["Normal"],
            fontName=base_font_bold,
            fontSize=12,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
        ),
        alias="h3",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading4",
            parent=stylesheet["Normal"],
            fontName=base_font_bold_italic,
            fontSize=10,
            leading=12,
            spaceBefore=10,
            spaceAfter=4,
        ),
        alias="h4",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading5",
            parent=stylesheet["Normal"],
            fontName=base_font_bold,
            fontSize=9,
            leading=10.8,
            spaceBefore=8,
            spaceAfter=4,
        ),
        alias="h5",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading6",
            parent=stylesheet["Normal"],
            fontName=base_font_bold,
            fontSize=7,
            leading=8.4,
            spaceBefore=6,
            spaceAfter=2,
        ),
        alias="h6",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Bullet",
            parent=stylesheet["Normal"],
            firstLineIndent=0,
            spaceBefore=3,
        ),
        alias="bu",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Definition",
            parent=stylesheet["Normal"],
            firstLineIndent=0,
            leftIndent=36,
            bulletIndent=0,
            spaceBefore=6,
            bulletFontName=base_font_bold_italic,
        ),
        alias="df",
    )

    stylesheet.add(
        ParagraphStyle(
            name="Code",
            parent=stylesheet["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=8.8,
            firstLineIndent=0,
            leftIndent=36,
            hyphenationLang="",
        )
    )

    stylesheet.add(
        ListStyle(
            name="UnorderedList",
            parent=None,
            leftIndent=18,
            rightIndent=0,
            bulletAlign="left",
            bulletType="1",
            bulletColor=black,
            bulletFontName="Helvetica",
            bulletFontSize=12,
            bulletOffsetY=0,
            bulletDedent="auto",
            bulletDir="ltr",
            bulletFormat=None,
            start=None,
        ),
        alias="ul",
    )

    stylesheet.add(
        ListStyle(
            name="OrderedList",
            parent=None,
            leftIndent=18,
            rightIndent=0,
            bulletAlign="left",
            bulletType="1",
            bulletColor=black,
            bulletFontName="Helvetica",
            bulletFontSize=12,
            bulletOffsetY=0,
            bulletDedent="auto",
            bulletDir="ltr",
            bulletFormat=None,
            start=None,
        ),
        alias="ol",
    )

    return stylesheet
