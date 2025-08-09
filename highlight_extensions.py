from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
from markdown import Markdown
import xml.etree.ElementTree as etree

class WarningHighlightProcessor(InlineProcessor):
    SPAN_CLASS = "text-warning"
    def handleMatch(self, m, data):
        el = etree.Element("span")
        el.text = m.group(1)
        el.attrib["class"] = self.SPAN_CLASS
        return el, m.start(0), m.end(0)

class WarningHighlightExtension(Extension):
    """Extension to convert *! this pattern !* to <span style='text-warning'> this pattern </span>"""

    def extendMarkdown(self, md):
        WARNING_HIGHLIGHT_PATTERN = r"\*!(.*?)!\*"  # match *! a pattern like this *!

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(WarningHighlightProcessor(WARNING_HIGHLIGHT_PATTERN, md), "warning_highlight", 64)



class TextHighlightProcessor(InlineProcessor):
    SPAN_CLASS_PARTIAL = "text-highlight-"
    def handleMatch(self, m, data):
        el = etree.Element("span")
        el.text = m.group(2)
        el.attrib["class"] = self.SPAN_CLASS_PARTIAL + m.group(1)
        return el, m.start(0), m.end(0)

class TextHighlightExtension(Extension):
    """Extension to convert *N! this pattern !* to <span style='text-highlight-N'> this pattern </span>, where N is a number"""

    def extendMarkdown(self, md):
        TEXT_HIGHLIGHT_PATTERN = r"\*(\d)+!(.*?)!\*"  # match *N! a pattern like this *! where N is a number

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(TextHighlightProcessor(TEXT_HIGHLIGHT_PATTERN, md), "text_highlight", 65)



class UnsureHighlightExtension(Extension):
    """Extension to convert *! this pattern !* to <span style='text-unsure'> this pattern </span>"""
    def extendMarkdown(self, md):
        UNSURE_HIGHLIGHT_PATTERN = r"\*\?(.*?)\?\*" # match *? a pattern like this ?*

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(UnsureHighlightProcessor(UNSURE_HIGHLIGHT_PATTERN, md, self), "unsure_highlight", 66)

    def __init__(self, **kwargs):
        self.config = {
            'superscript': ["", "Superscript to show after the text"],
            'tooltip': ["", "Tooltip to show when hovering on the superscript"],
        }
        super(UnsureHighlightExtension, self).__init__(**kwargs)


class UnsureHighlightProcessor(InlineProcessor):
    SPAN_CLASS = "text-unsure"

    def handleMatch(self, m, data):
        el = etree.Element('span')
        el.text = m.group(1)
        el.attrib["class"] = self.SPAN_CLASS
        if self.superscript != "":
            e2 = etree.SubElement(el, 'sup')
            e2.text = self.superscript
            if self.tooltip != "":
                e2.attrib["title"] = self.tooltip
        return el, m.start(0), m.end(0)

    def __init__(self, pattern: str, md: Markdown, ext: UnsureHighlightExtension):
        super().__init__(pattern)
        self.md = md

        self.superscript = ext.getConfig("superscript")
        self.tooltip = ext.getConfig("tooltip")
