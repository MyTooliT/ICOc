# -- Imports ------------------------------------------------------------------

from reportlab.lib.styles import (_baseFontName, _baseFontNameB,
                                  _baseFontNameI, _baseFontNameBI, ListStyle,
                                  ParagraphStyle, StyleSheet1)
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER

# -- Functions ----------------------------------------------------------------


def getStyleSheet() -> StyleSheet1:
    """Get the default style sheet for PDF reports

    This is more or less a slightly modified version of the
    function `getSampleStyleSheet` shipped with ReportLab.
    """

    stylesheet = StyleSheet1()

    stylesheet.add(
        ParagraphStyle(name='Normal',
                       fontName=_baseFontName,
                       fontSize=10,
                       leading=12))

    stylesheet.add(
        ParagraphStyle(name='BodyText',
                       parent=stylesheet['Normal'],
                       spaceBefore=6))
    stylesheet.add(
        ParagraphStyle(name='Italic',
                       parent=stylesheet['BodyText'],
                       fontName=_baseFontNameI))

    stylesheet.add(ParagraphStyle(name='Heading1',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=18,
                                  leading=22,
                                  spaceAfter=6),
                   alias='h1')

    stylesheet.add(ParagraphStyle(name='Title',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=18,
                                  leading=22,
                                  alignment=TA_CENTER,
                                  spaceAfter=6),
                   alias='title')

    stylesheet.add(ParagraphStyle(name='Heading2',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=14,
                                  leading=18,
                                  spaceBefore=12,
                                  spaceAfter=6),
                   alias='h2')

    stylesheet.add(ParagraphStyle(name='Heading3',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=12,
                                  leading=14,
                                  spaceBefore=12,
                                  spaceAfter=6),
                   alias='h3')

    stylesheet.add(ParagraphStyle(name='Heading4',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameBI,
                                  fontSize=10,
                                  leading=12,
                                  spaceBefore=10,
                                  spaceAfter=4),
                   alias='h4')

    stylesheet.add(ParagraphStyle(name='Heading5',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=9,
                                  leading=10.8,
                                  spaceBefore=8,
                                  spaceAfter=4),
                   alias='h5')

    stylesheet.add(ParagraphStyle(name='Heading6',
                                  parent=stylesheet['Normal'],
                                  fontName=_baseFontNameB,
                                  fontSize=7,
                                  leading=8.4,
                                  spaceBefore=6,
                                  spaceAfter=2),
                   alias='h6')

    stylesheet.add(ParagraphStyle(name='Bullet',
                                  parent=stylesheet['Normal'],
                                  firstLineIndent=0,
                                  spaceBefore=3),
                   alias='bu')

    stylesheet.add(ParagraphStyle(name='Definition',
                                  parent=stylesheet['Normal'],
                                  firstLineIndent=0,
                                  leftIndent=36,
                                  bulletIndent=0,
                                  spaceBefore=6,
                                  bulletFontName=_baseFontNameBI),
                   alias='df')

    stylesheet.add(
        ParagraphStyle(name='Code',
                       parent=stylesheet['Normal'],
                       fontName='Courier',
                       fontSize=8,
                       leading=8.8,
                       firstLineIndent=0,
                       leftIndent=36,
                       hyphenationLang=''))

    stylesheet.add(ListStyle(
        name='UnorderedList',
        parent=None,
        leftIndent=18,
        rightIndent=0,
        bulletAlign='left',
        bulletType='1',
        bulletColor=black,
        bulletFontName='Helvetica',
        bulletFontSize=12,
        bulletOffsetY=0,
        bulletDedent='auto',
        bulletDir='ltr',
        bulletFormat=None,
        start=None,
    ),
                   alias='ul')

    stylesheet.add(ListStyle(
        name='OrderedList',
        parent=None,
        leftIndent=18,
        rightIndent=0,
        bulletAlign='left',
        bulletType='1',
        bulletColor=black,
        bulletFontName='Helvetica',
        bulletFontSize=12,
        bulletOffsetY=0,
        bulletDedent='auto',
        bulletDir='ltr',
        bulletFormat=None,
        start=None,
    ),
                   alias='ol')

    return stylesheet
