from markdown import Markdown
from markdown.inlinepatterns import InlineProcessor, IMAGE_LINK_RE, LinkInlineProcessor
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import xml.etree.ElementTree as etree
import re
import markdown

class SmallImageProcessor(LinkInlineProcessor):
    DIV_CLASS = "small-img"

    # Adapted from markdown.inlinepatterns.ImageProcessor
    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element | None, int | None, int | None]:
        """ Return an `img` [`Element`][xml.etree.ElementTree.Element] or `(None, None, None)`. """
        text, index, handled = self.getText(data, m.end(0))
        if not handled:
            return None, None, None

        src, title, index, handled = self.getLink(data, index)
        if not handled:
            return None, None, None

        e = etree.Element("a")
        el = etree.SubElement(e, "img")

        el.set("src", src)
        e.set("href", src)
        e.set("target", "_blank")
        el.set("class", self.DIV_CLASS)

        if title is not None:
            el.set("title", title)

        el.set('alt', self.unescape(text))
        return e, m.start(0), index

class SmallImageExtension(Extension):
    """Extension to convert *! this pattern !* to <span style='text-warning'> this pattern </span>"""
    def extendMarkdown(self, md):
        SMALL_IMAGE_PATTERN = r'!!\['

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(SmallImageProcessor(SMALL_IMAGE_PATTERN, md), "small_image", 175) # !Priority higher than the stock image parser
