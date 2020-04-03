import operator
import sly
from sly import Lexer, Parser
from SyQuery.exceptions import SynamicQueryParsingError
from syd.curlybrace_parser import SydParser  #covert_one_value
from collections import namedtuple

from SyQuery.parser.query_node import FilterNode


def generate_error_message(text, text_rest):
    err_before_txt = '_' * (len(text) - len(text_rest))
    err_after_txt = '^' * len(text_rest)
    err_txt = '\n' + text + '\n' + err_before_txt + err_after_txt
    return err_txt


class SimpleQueryParser:
    COMPARE_OPERATORS = tuple([
        'contains',
        '!contains',
        'in',
        '!in',
        '==',
        '!=',
        '>=',
        '<=',
        '>',
        '<',
    ])

    COMPARE_OPERATORS_SET = frozenset(COMPARE_OPERATORS)

    COMPARE_OPERATOR_2_PY_OPERATOR_FUN = {
        'contains': operator.contains,
        '!contains': lambda a, b: not operator.contains(a, b),
        'in': lambda a, b: operator.contains(b, a),
        '!in': lambda a, b: not operator.contains(b, a),
        '==': operator.eq,
        '!=': operator.ne,
        '>=': operator.ge,
        '<=': operator.le,
        '>': operator.gt,
        '<': operator.lt
    }

    Query = namedtuple('Query', ('node', 'sort'))
    QuerySection = namedtuple('QuerySection', ('key', 'comp_op', 'value'))
    QuerySortBy = namedtuple('QuerySortBy', ('by_key', 'order'))

    def __init__(self, txt):
        self.__txt = txt

    def parse(self):
        """
        title == something | type in go, yes & age > 6
        """
        text = self.__txt.strip()
        lexer = QueryLexer()
        parser = QueryParser(text)
        try:
            if text == '':
                res = self.Query(None, None)
            else:
                res = parser.parse(lexer.tokenize(text))

            if len(res) == 1:
                if isinstance(res[0], self.QuerySortBy):
                    query = self.Query(node=None, sort=res[0])
                else:
                    query = self.Query(node=res[0], sort=None)
            else:
                assert len(res) > 1
                query = self.Query(node=res[0], sort=res[1])
        except sly.lex.LexError as e:
            err_txt = generate_error_message(text, e.text)
            raise SynamicQueryParsingError(
                f'Lexical error at index: {e.error_index}\nDetails:{err_txt}'
            )
        else:
            return query


class QueryValueLexer(Lexer):
    tokens = {'VALUE', }

    @_(r'[^&|:]+')
    def VALUE(self, t):
        self.begin(QueryLexer)
        t.value = t.value.strip()
        return t


class QueryLexer(Lexer):
    tokens = {'KEY', 'COMP_OP', 'AND', 'OR', 'SORT_BY'}
    ignore_ws = r'\s'
    SORT_BY = r':sortby\s+'

    @_(r'>|<|==|!=|>=|<=|\s+in|!in|\s+contains|!contains')
    def COMP_OP(self, t):
        self.begin(QueryValueLexer)
        t.value = t.value.strip()
        return t

    KEY = r'[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*'

    KEY['contains'] = 'COMP_OP'
    KEY['in'] = 'COMP_OP'

    @_(r'&')
    def AND(self, t):
        return t

    @_(r'\|')
    def OR(self, t):
        return t


class QueryParser(Parser):
    def __init__(self, text):
        self.__text = text

    # Get the token list from the lexer (required)
    tokens = {*QueryLexer.tokens, *QueryValueLexer.tokens}
    precedence = [
        ('left', 'OR'),
        ('left', 'AND'),
    ]

    # Grammar rules and actions
    @_('expr',
       'sort',
       'expr sort')
    def query(self, p):
        if len(p) == 1:
            return p[0],
        else:
            return p[0], p[1]

    @_('SORT_BY KEY',
       'SORT_BY KEY KEY')
    def sort(self, p):
        if len(p) == 2:
            order = 'asc'
        else:
            if p[2].startswith('a'):
                order = 'asc'
            else:
                order = 'desc'
        return SimpleQueryParser.QuerySortBy(by_key=p[1], order=order)

    @_('KEY COMP_OP VALUE')
    def expr(self, p):
        converted_value = SydParser.covert_one_value(p[2])
        return SimpleQueryParser.QuerySection(key=p[0], comp_op=p[1], value=converted_value)

    @_('expr OR expr',
       'expr AND expr')
    def expr(self, p):
        left_section, right_section = p[0], p[2]
        return FilterNode(left_section, p[1], right_section)

    def error(self, p):
        text = self.__text
        if not p:
            text_rest = ''
            err_txt = generate_error_message(text, text_rest)
            err = SynamicQueryParsingError(
                f'End of query string before tokens could be parsed sensibly.\nDetails:{err_txt}'
            )
        else:
            text_rest = self.__text[p.index:]
            err_txt = generate_error_message(text, text_rest)
            err = SynamicQueryParsingError(
                f'Parsing error at token {p.type}.\nDetails:{err_txt}'
            )
        raise err
