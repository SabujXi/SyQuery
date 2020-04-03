from unittest import TestCase
from SyQuery.parser.parser import YaccQueryParser


class TestSimpleQueryParser(TestCase):
    def test_parsing(self):
        query = 'up sort asc | x == 1&time > 11:24 PM | date == 2013-2-1 | dt < 1023-12-12     11:33:43 am | a > b & c in d | d in ~hh        & m contains tag 1, tag 2 & n !in go sfsdfsdf'
        tokens = SimpleQueryParser(query).parse()
        for token in tokens:
            print(token)
