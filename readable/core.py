
"""
readable - a direct port of Arc90's readability content extraction rules.
Original:  http://lab.arc90.com/experiments/readability

In order to simplify this port, the style adheres as closely as possible to the
original Javascript source. Methods are implemented in the same order  as the
original source, and have been commented with corresponding line numbers.

However, in order to keep the code clear and 'readable', some routines with
high complexity have been extracted into separate methods and marked
accordingly.

This approach will be maintained until there is sufficient test cases to ensure
the code does not drift from the original implementation.

Author: Patrick Hensley <spaceboy@indirect.com>
License: http://www.apache.org/licenses/LICENSE-2.0
"""

__version__ = '0.1'
UPSTREAM_VERSION = '1.7.1'      # cloned 11/14/2010


# std
import math
import re
import sys

# vendor
import lxml.html
import lxml.html.clean


__pychecker__ = 'no-objattrs'


# line 54

# class and id patterns
RE_UNLIKELY = re.compile('combx|comment|community|disqus|extra|foot|'
    'header|menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|'
    'pagination|pager|popup|tweet|twitter', re.I)
RE_MAYBE = re.compile('and|article|body|column|main|shadow', re.I)
RE_POSITIVE = re.compile('article|body|content|entry|hentry|main|page|'
    'pagination|post|text|blog|story', re.I)
RE_NEGATIVE = re.compile('combx|comment|com-|contact|foot|footer|'
    'footnote|masthead|media|meta|outbrain|promo|related|scroll|'
    'shoutbox|sidebar|sponsor|shopping|tags|tool|widget', re.I)


# markup and text formatting
_REPL_PARAS = ['a','blockquote','dl','div','img','ol','p','pre','table','ul']
XPATH_REPL_PARAS = '|'.join([('.//%s' % t) for t in _REPL_PARAS])
RE_SENT = re.compile('\.( |$)')
RE_NORMALIZE = re.compile('\s{2,}')
RE_VIDEOS = re.compile('http:\/\/(www\.)?(youtube|vimeo)\.com', re.I)


class Bag(object):

    "Generic sticky object."

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __setattr__(self, key, val):
        self.__dict__[key] = val

    def __str__(self):
        r = ' '.join('%s=%s' % (k, repr(v)) for k, v in self.__dict__.items())
        return '<Bag ' + r + '>'


class NodeIter(object):

    "Mimic the behavior of browser's 'node list' iterator / array."

    def __init__(self, root):
        self.root = root
        self.nodes = list(root.iterdescendants())
        self.idx = 0
        self.current = None

    def __iter__(self):
        return self

    def next(self):
        if self.idx >= len(self.nodes):
            raise StopIteration()
        node = self.nodes[self.idx]
        self.current = node
        self.idx += 1
        return self.idx, node

    def remove(self):
        """
        When a node is removed from the browser's DOM it disappears from the
        nodelist as do all it's descendants, and the iterator skips over those
        removed nodes.
        """
        curr = self.current
        if curr is None:
            return
        curr.getparent().remove(curr)
        oldlen = len(self.nodes)
        self.nodes = list(self.root.iterdescendants())
        self.idx -= 1


class Readable(object):

    """
    Implementation of readability's content extraction rules.
    """

    FLAG_NONE = 0x0
    FLAG_STRIP_UNLIKELY = 0x01
    FLAG_CLASS_WEIGHT = 0x02
    FLAG_CLEAN_CONDITIONALLY = 0x04

    FLAGS = [
        FLAG_NONE,
        FLAG_STRIP_UNLIKELY,
        FLAG_CLASS_WEIGHT,
        FLAG_CLEAN_CONDITIONALLY
        ]

    def __init__(self, debug=0):
        self.debug = debug
        self.flags = 0xFFFF

    def log(self, msg):
        "Mimic use of console.log"
        if not self.debug:
            return
        sys.stderr.write("Readable: " + msg + '\n')
        sys.stderr.flush()

    def is_unlikely(self, node):
        "Return whether 'node' is unlikely and should be removed."
        if not (self.flags & self.FLAG_STRIP_UNLIKELY):
            return 0
        if node.tag == 'body':
            return 0
        ms = ''.join(self.get_clsid(node))
        if RE_UNLIKELY.search(ms) and not RE_MAYBE.search(ms):
            return 1
        return 0

    def is_readable(self, node):
        "Returns a boolean indicating that 'node' has been marked"
        return hasattr(node, 'readable')

    def get_clsid(self, node):
        "Return a tuple of the 'class' and 'id' attributes for 'node'."
        return node.get('class', ''), node.get('id', '')

    def get_info(self, node):
        "Return a string 'TAG (CLASS:ID)' for 'node'"
        ncls, nid = self.get_clsid(node)
        return '%s (%s:%s)' % (node.tag, ncls, nid)

    def get_path(self, node):
        "Return a string representing the path to 'node' in the tree."
        if node is None or node.tag == 'html':
            return 'html'
        return self.get_path(node.getparent()) + ' / ' + self.get_info(node)

    def make_cleaner(self):
        "Construct an object to clean out unwanted stuff from a node."
        opts = dict(scripts=True, javascript=True, comments=True,
            style=True, links=True, meta=False, page_structure=False, 
            processing_instructions=True, embedded=False, frames=False, 
            forms=False, annoying_tags=False, safe_attrs_only=False)
        return lxml.html.clean.Cleaner(**opts)

    def node_copy(self, node):
        "Make a copy of a node, copying its attributes and children."
        newn = lxml.html.Element(node.tag, node.attrib)
        newn.text = node.text
        newn.tail = node.tail
        for c in node.getchildren():
            newc = self.node_copy(c)
            newn.append(newc)
        return newn


    # line 185
    # init

    # line 226
    # postProcessContent

    # line 242
    # fixImageFloats

    # line 260
    # getArticleTools

    # line 274
    # getSuggestedDirection  - handles hebrew, right-to-left langs.

    # line 301
    # getArticleTitle 

    # line 353
    # getArticleFooter

    # line 375
    def prep_document(self, data):
        "Prep the document for extraction"
        tree = lxml.html.fromstring(data)
        # clean unknown tags out
        cleaner = self.make_cleaner()
        cleaner(tree)
        body = tree.find('body')
        if body is None:
            self.log(lxml.html.tostring(tree))
            body = lxml.html.Element('body')
            for n in tree.getchildren():
                body.append(n)
            tree.append(body)
        body.attrib['id'] = 'readableBody'

        # kill all non-body siblings for extraction
        for n in body.getparent().getchildren():
            if n.tag != 'body':
                n.getparent().remove(n)

        return self.convert_brs(body)


    # line 461 
    # addFootnotes

    # line 537
    # useRdbTypekit 


    # line 601
    def prep_article(self, content):
        "Prepare 'content' for display."
        self.clean_styles(content)
        self.clean_conditionally(content, "form")
        self.clean(content, 'object')
        self.clean(content, 'h1')
        if len(content.xpath('.//h2')) == 1:
            self.clean(content, 'h2')
        self.clean(content, 'iframe')
        self.clean_headers(content)

        self.clean_conditionally(content, 'table')
        self.clean_conditionally(content, 'ul')
        self.clean_conditionally(content, 'div')
 
        # line 626: remove extra paragraphs
        for n in content.xpath('.//p'):
            num_img = n.xpath('.//img')
            num_embed = n.xpath('.//embed')
            num_object = n.xpath('.//object')
            if num_img == 0 and num_embed == 0 and num_object == 0:
                if self.get_inner_text(n, 0):
                    n.getparent().remove(n)
        # line 639
        # kill breaks already done above


    # line 653
    def initialize_node(self, node):
        "Add readable's attributes to 'node'."
        score = 0
        if node is None:
            return
        if node.tag == 'div':
            score += 5
        elif node.tag in set(['pre','td','blockquote']):
            score += 3
        elif node.tag in set(['address','ol','ul','dl','dd','dt','li','form']):
            score -= 3
        elif node.tag in set(['h1','h2','h3','h4','h5','h6','th']):
            score -= 5
        score += self.get_class_weight(node)
        node.readable = Bag(score=score)


    # line 701
    def _grab_article(self, data):
        """
        This performs the core extraction, and is potentially called by
        'grab_article' multiple times, relaxing extraction flags on each
        pass.
        """
        body = self.prep_document(data)

        # line 720 - 766 - moved into method 'select_scorable'
        to_score = self.select_scorable(body)
        
        # line 774
        content = self.score_paras(to_score, body)
        return content


    # line 720
    def convert_brs(self, node):
        "Convert all text that is siblings of <br> tags to <p>"
        # TODO: i prefer doing dom-based replacement of brs to using
        # regexps, but this needs to be simplified.
        children = node.getchildren()
        has_br = 'br' in [n.tag for n in children]
        if has_br:
            newn = lxml.html.Element(node.tag, node.attrib)
            if node.text and node.text.strip():
                c = lxml.html.Element('p')
                c.text = node.text
                node.text = ''
                newn.append(c)
            for n in children:
                if n.tag == 'br':
                    # snip the trailing text from the br
                    if n.tail and n.tail.strip():
                        c = lxml.html.Element('p')
                        c.text = n.tail
                        newn.append(c)
                    continue
                newn.append(n)
                if n.tail and n.tail.strip():
                    c = lxml.html.Element('p')
                    c.text = n.tail
                    n.tail = ''
                    newn.append(c)
            if node.tail and node.tail.strip():
                c = lxml.html.Element('p')
                c.text = node.tail
                newn.append(c)
            node.getparent().replace(node, newn)
            node = newn
        for n in node.getchildren():
            self.convert_brs(n)
        return node


    def select_scorable(self, node):
        "Iterate over descendants and select some for scoring."
        to_score = []
        nodeiter = NodeIter(node)
        para_attrs = {'class': 'readable-styled'}
        for idx, n in nodeiter:
            if self.is_unlikely(n):
                self.log('Removing unlikely candidate - ' + self.get_info(n))
                nodeiter.remove()
                continue

            # line 733
            if n.tag in set(['p', 'td', 'pre']):
                to_score.append(n)

            # line 738
            if n.tag == 'div':
                if not n.xpath(XPATH_REPL_PARAS):
                    newn = self.node_copy(n)
                    newn.tag = 'p'
                    n.getparent().replace(n, newn)
                    to_score.append(n)
                    to_score.append(newn)
                else:
                    to_score += self._paragraphize_text(n)

        return to_score


    # line 754 (marked EXPERIMENTAL)
    def _paragraphize_text(self, node):
        "Wraps text children of 'node' in <p>"
        to_score = []
        newn = lxml.html.Element(node.tag, node.attrib)
        if node.text:
            el = lxml.html.Element('p')
            el.text = node.text
            node.text = ''
            newn.append(el)
            to_score.append(el)
        for c in node.getchildren():
            newn.append(c)
            if c.tail:
                el = lxml.html.Element('p')
                el.text = c.tail
                c.tail = ''
                newn.append(el)
                to_score.append(el)
        if node.tail:
            el = lxml.html.Element('p')
            el.text = node.tail
            node.tail = ''
            newn.append(el)
            to_score.append(el)
        node.getparent().replace(node, newn)
        return to_score


    # line 775
    def score_paras(self, nodes, body):
        "Score all 'nodes' according to various metrics."
        candidates = []
        for n in nodes:
            parent = n.getparent()
            if parent is None:
                continue
            gparent = None
            if parent is not None:
                gparent = parent.getparent()
            text = self.get_inner_text(n)
            if len(text) < 25:
                continue
            if parent is not None and not self.is_readable(parent):
                self.initialize_node(parent)
                candidates.append(parent)
            if gparent is not None and not self.is_readable(gparent):
                self.initialize_node(gparent)
                candidates.append(gparent)

            # line 809
            score = 0
            score += 1
            score += len(text.split(','))
            score += min(math.floor(len(text) / 100.0), 3)
            parent.readable.score += score
            if gparent is not None:
                gparent.readable.score += score / 2.0

        return self._select_top(candidates, body)


    # extracted from 'score_paras'
    def _select_top(self, candidates, body):
        "Select the top (best) node from the candidates."
        # line 824
        top = None
        for n in candidates:
            n.readable.score *= (1 - self.get_link_density(n))
            self.log('Candidate: ' + self.get_info(n) + 
                ' with score %.2f' % n.readable.score)
            if top is None or (n.readable.score > top.readable.score):
                top = n

        # line 843
        content = lxml.html.Element('div')
        if top is None or top.tag == 'body':
            top = lxml.html.Element('div')
            for n in body.getchildren():
                top.append(n)
            body.append(top)
            self.initialize_node(top)
            self.initialize_node(body)

        # line 859
        sib_thresh = max(10, top.readable.score * 0.2)

        # loop over siblings of 'top', looking for any that are promising.
        for n in top.getparent().getchildren():
            append = 0
            if n is None:
                continue

            # line 874
            # logging to match that found in original source
            msg = 'Looking at sibling node: ' + self.get_info(n)
            if self.is_readable(n):
                msg += ' with score %.2f' % n.readable.score
            self.log(msg)
            msg = "Sibling has score "
            if self.is_readable(n):
                msg += '%.2f' % n.readable.score
            else:
                msg += 'Unknown'
            self.log(msg)

            if n == top:
                append = 1

            # line 881
            bonus = 0
            tclass = top.get('class', '')
            nclass = n.get('class', '')
            if nclass == tclass and tclass:
                bonus += top.readable.score * 0.2
            if self.is_readable(n) and (n.readable.score + bonus) >= sib_thresh:
                append = 1

            # line 891
            if n.tag == 'p':
                link_density = self.get_link_density(n)
                text = self.get_inner_text(n)
                text_len = len(text)
                if text_len > 80 and link_density < 0.25:
                    append = 1
                elif text_len < 80 and link_density == 0 and \
                        RE_SENT.search(text):
                    append = 1

            # line 904
            if append:
                if n.tag not in ('div', 'p'):
                    n.tag = 'div'
                content.append(n)

        self.prep_article(content)
        return content


    # line 952
    def grab_article(self, data):
        "Find the readable content in 'data', a string containing HTML."
        flags = list(self.FLAGS)
        flags.reverse()
        content = None
        text = ''
        while len(text) < 250:
            flag = flags.pop()
            self.flags &= ~flag
            content = self._grab_article(data)
            # if no more flags can be cleared, take what we can get
            if not flags:
                break
            text = self.get_inner_text(content, 0)
        return content


    # line 979
    # removeScripts


    # line 999
    def get_inner_text(self, node, normalize_spaces=1, depth=0):
        "Recursively retrieve all text from this node."
        text = ''
        if node.text:
            text = ' ' + node.text
        for n in node.getchildren():
            text += self.get_inner_text(n, normalize_spaces, depth + 1)
        if node.tail:
            text += ' ' + node.tail
        # run normalize once on final text.
        if normalize_spaces and not depth:
            text = RE_NORMALIZE.sub(' ', text)
        return text


    # line 1030
    def get_char_count(self, node, char):
        return len(self.get_inner_text(node).split(char)) - 1


    # line 1042
    def clean_styles(self, node):
        if 'style' in node.attrib:
            del node.attrib['style']
        for n in list(node.iterchildren()):
            self.clean_styles(n)


    # line 1075
    def get_link_density(self, node):
        links = node.xpath('.//a')
        textlen = len(self.get_inner_text(node))
        if textlen == 0:
            return 0
        linklen = 0
        for link in links:
            linklen += len(self.get_inner_text(link))
        return linklen / float(textlen)


    # line 1092
    # findBaseUrl - part of "next page downloading"

    # line 1157
    # findNextPageLink - paging function. may implement this eventually as part
    # of another layer, e.g. when the page is downloaded do a quick scan for
    # the next page, download it, then extract each of the N pages using
    # readable.

    # line 1329
    # xhr - part of "next page downloading"

    # line 1348
    # successfulRequest - part of "next page downloading"

    # line 1352
    # ajax - part of "next page downloading"
    
    # line 1396
    # appendNextPage - part of "next page downloading"


    # line 1512
    def get_class_weight(self, node):
        if not (self.flags & self.FLAG_CLASS_WEIGHT):
            return 0
        weight = 0
        ncls, nid = self.get_clsid(node)
        if ncls:
            if RE_NEGATIVE.search(ncls):
                weight -= 25
            if RE_POSITIVE.search(ncls):
                weight += 25
        if nid:
            if RE_NEGATIVE.search(nid):
                weight -= 25
            if RE_POSITIVE.search(nid):
                weight += 25
        return weight


    # line 1544
    # nodeIsVisible - not in use by the algorithm


    # line 1554
    # killBreaks - not in use


    # line 1571
    def clean(self, node, tag):
        targets = node.xpath('.//%s' % tag)
        is_embed = tag in ('object','embed')
        for n in targets:
            if is_embed:
                vals = '|'.join(n.attrib.values())
                if RE_VIDEOS.search(vals):
                    continue
            n.getparent().remove(n)


    # line 1605
    def clean_conditionally(self, node, tag):
        if not (self.flags & self.FLAG_CLEAN_CONDITIONALLY):
            return
        nodes = node.xpath('.//%s' % tag)
        for n in nodes:
            if n == node:
                continue
            weight = self.get_class_weight(n)
            score = 0

            # line 1624
            msg = 'Cleaning Conditionally ' + str(n) + ' (' + \
                n.get('class', '') + ':' + n.get('id', '') + ')'
            if self.is_readable(n):
                msg += ' with score %.2f' % n.readable.score
            self.log(msg)

            if self.is_readable(n):
                score = n.readable.score
            if weight + score < 0:
                n.getparent().remove(n)
            elif self.get_char_count(n, ',') < 10:
                num_p = len(n.xpath('.//p'))
                num_img = len(n.xpath('.//img'))
                num_li = len(n.xpath('.//li')) - 100
                num_input = len(n.xpath('.//input'))
                num_embeds = 0
                for em in n.xpath('.//embed'):
                    if RE_VIDEOS.search(em.get('src', '')):
                        num_embeds += 1
                link_density = self.get_link_density(n)
                len_content = len(self.get_inner_text(n))
                
                # line 1649
                to_remove = 0
                if num_img > num_p:
                    to_remove = 1
                elif num_li > num_p and tag not in ('ul','ol'):
                    to_remove = 1
                elif num_input > math.floor(num_p / 3.0):
                    to_remove = 1
                elif len_content < 25 and (num_img == 0 or num_img > 2):
                    to_remove = 1
                    self.log(lxml.html.tostring(n))
                elif weight < 25 and link_density > 0.2:
                    to_remove = 1
                elif weight >= 25 and link_density > 0.5:
                    to_remove = 1
                elif (num_embeds == 1 and len_content < 75) or num_embeds > 1:
                    to_remove = 1
                if to_remove:
                    n.getparent().remove(n)


    # line 1680
    def clean_headers(self, node):
        for i in range(0, 3):
            for n in node.xpath('.//h%d' % i):
                cw = self.get_class_weight(n)
                ld = self.get_link_density(n)
                if cw < 0 or ld > 0.33:
                    n.getparent().remove(n)


    # line 1698 - animation and display functions.
    # easeInOut 
    # scrollTop
    # scrollTo
    # emailBox
    # removeFrame
    # htmlspecialchars
    # flagIsActive
    # addFlag
    # removeFlag

