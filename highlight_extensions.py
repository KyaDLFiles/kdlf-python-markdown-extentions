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
        md.inlinePatterns.register(WarningHighlightProcessor(WARNING_HIGHLIGHT_PATTERN, md), "warning_highlight", 65)



class UnsureHighlightExtension(Extension):
    """Extension to convert *! this pattern !* to <span style='text-unsure'> this pattern </span>"""
    def extendMarkdown(self, md):
        UNSURE_HIGHLIGHT_PATTERN = r"\*\?(.*?)\?\*" # match *? a pattern like this ?*

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(UnsureHighlightProcessor(UNSURE_HIGHLIGHT_PATTERN, md), "unsure_highlight", 66)

    def __init__(self, **kwargs):
        self.config = {
            'superscript': ["", "Superscript to show after the text"],
            'tooltip': ["", "Tooltip to show when hovering on the superscript"],
        }
        """ Default configuration options. """

        super().__init__(**kwargs)


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
