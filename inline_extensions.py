from markdown.inlinepatterns import LinkInlineProcessor, NOIMG
from markdown.extensions import Extension
from markdown import Markdown
from xml.etree import ElementTree as etree
import re

LINK_RE_BLANK = NOIMG + r'\?\['

class LinkBlankInlineExtension(Extension):
    """Adds support for links with target="_blank" by using ?[]()
    Takes extra_text as a config parameter to add extra text at the end of the links"""
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(LinkBlankInlineProcessor(LINK_RE_BLANK, md, self), "link_blank", 165)

    def __init__(self, **kwargs):
        self.config = {
            #TODO: idk what the first item in the list does
            "extra_text": ["", "Extra text to add at the end of links"],
        }
        super(LinkBlankInlineExtension, self).__init__(**kwargs)

class LinkBlankInlineProcessor(LinkInlineProcessor):
    def __init__(self, pattern: str, md: Markdown, ext: LinkBlankInlineExtension):
        super().__init__(pattern)
        self.md = md

        self.extra_text = ext.getConfig("extra_text")

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element | None, int | None, int | None]:
        ret = super().handleMatch(m, data)
        if ret[0] is not None:
            ret[0].attrib["target"] = "_blank"
            ret[0].attrib["rel"] = "noreferrer noopener"
            ret[0].text += self.extra_text
        return ret