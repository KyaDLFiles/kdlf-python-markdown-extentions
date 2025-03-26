class UnsureSpanProcessor(InlineProcessor):
    SPAN_CLASS = "text-warning"
    def handleMatch(self, m, data):
        el = etree.Element("span")
        el.text = m.group(1)
        el.attrib["class"] = self.SPAN_CLASS
        return el, m.start(0), m.end(0)

class UnsureSpanExtension(Extension):
    """Extension to convert *! this pattern !* to <span style='text-warning'> this pattern </span>"""
    def extendMarkdown(self, md):
        WARNING_HIGHLIGHT_PATTERN = r"\*!(.*?)!\*" # match *! a pattern like this *!

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(UnsureSpanProcessor(WARNING_SPAN_PATTERN, md), "warning_highlight", 175)

class UnsureHighlightProcessor(InlineProcessor):
    SPAN_CLASS = "text-unsure"
    def handleMatch(self, m, data):
        el = etree.Element('span')
        el.text = m.group(1)
        el.attrib["class"] = self.SPAN_CLASS
        return el, m.start(0), m.end(0)

class UnsureHighlightExtension(Extension):
    """Extension to convert *! this pattern !* to <span style='text-unsure'> this pattern </span>"""
    def extendMarkdown(self, md):
        UNSURE_HIGHLIGHT_PATTERN = r"\*\?(.*?)\?\*" # match *? a pattern like this ?*

        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(UnsureHighlightProcessor(UNSURE_SPAN_PATTERN, md), "unsure_highlight", 175)

