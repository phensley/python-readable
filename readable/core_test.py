

# std
import os
import re
import unittest

# vendor
import lxml.html

# local
import core


ROOT = os.path.dirname(os.path.abspath(__file__))
RE_SPACE = re.compile('\s+', re.M)


def get_data(name):
    global ROOT
    path = os.path.join(ROOT, 'testdata', name)
    fh = open(path, 'rb')
    data = fh.read()
    fh.close()
    return data


def get_tree(name):
    data = get_data(name)
    return lxml.html.fromstring(data)


class TestReadable(unittest.TestCase):

    def test_convert_brs(self):
        rb = core.Readable(debug=0)
        res = rb.convert_brs(get_tree('breaks_t.html'))
        exp = lxml.html.fromstring(get_data('breaks_e.html'))
        res = RE_SPACE.sub('', lxml.html.tostring(res))
        exp = RE_SPACE.sub('', lxml.html.tostring(exp))
        self.assertEquals(res, exp)


def main():
    unittest.main()


if __name__ == '__main__':
    main()

