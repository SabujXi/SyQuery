import operator
import sly
from sly import Lexer, Parser
from SyQuery.exceptions import SynamicQueryParsingError
from collections import namedtuple


def generate_error_message(text, text_rest):
    err_before_txt = '_' * (len(text) - len(text_rest))
    err_after_txt = '^' * len(text_rest)
    err_txt = '\n' + text + '\n' + err_before_txt + err_after_txt
    return err_txt


class SimpleQueryParser:
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


# class QueryValueLexer(Lexer):
#     tokens = {'VALUE', }
#
#     @_(r'[^&|:]+')
#     def VALUE(self, t):
#         self.begin(QueryLexer)
#         t.value = t.value.strip()
#         return t


class QueryLexer(Lexer):
    tokens = {'KEY', 'ACTION_KEY', 'COMP_OP', 'STRING', 'NUMBER', 'TIME', 'DATE', 'DATETIME', 'JOINING_OP', 'BRACE_OPEN', 'BRACE_CLOSE', 'COMMA', 'SQUARE_OPEN', 'SQUARE_CLOSE', 'PIPE'}
    ignore_ws = r'\s'

    BRACE_OPEN = r'\('
    BRACE_CLOSE = r'\)'
    SQUARE_OPEN = r'\['
    SQUARE_CLOSE = r']'
    PIPE = r'\|'

    KEY = r'[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*'
    KEY['contains'] = 'COMP_OP'
    KEY['in'] = 'COMP_OP'
    KEY['and'] = 'JOINING_OP'
    KEY['or'] = 'JOINING_OP'

    ACTION_KEY = r':[a-zA-Z0-9]+'

    @_(r'>|<|==|!=|>=|<=|\s+in|!in|\s+contains|!contains')
    def COMP_OP(self, t):
        # self.begin(QueryValueLexer)
        t.value = t.value.strip()
        return t

    @_(r'and|or')
    def JOINING_OP(self, t):
        return t

    @_(r'\d{1,2}:\d{1,2}\s*?(am|pm|AM|PM)?')
    def TIME(self, t):
        return t

    @_(r'\d{4}-\d{1,2}-\d{1,2}')
    def DATE(self, t):
        return t

    @_(r'\d{4}-\d{1,2}-\d{1,2}\s+'
       r'\d{1,2}:\d{1,2}\s*?(am|pm|AM|PM)?')
    def DATETIME(self, t):
        return t

    @_(
        r'(?P<quotechar>"|\')(\\(?P=quotechar)|.*?)*(?P=quotechar)'
        # numeric backreference cannot be used as sly lex "|".join()s all the regex and also make named groups of each
        # token
    )
    def STRING(self, t):
        if t.value:
            t.value = t.value[1:-1]
        return t

    @_(r'[+-]?[0-9]+(\.[0-9]+)?')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r',')
    def COMMA(self, t):
        return t


class QueryParser(Parser):
    def __init__(self, text):
        self.__text = text

    # Get the token list from the lexer (required)
    tokens = {*QueryLexer.tokens, }
    precedence = [
        ('left', 'SQUARE_OPEN'),
        ('left', 'COMP_OP'),
        # ('left', 'BRACE_OPEN'),
    ]

    # Grammar rules and actions
    @_(
        'filter_group',
        'filter_group action_group',
        'filter_group JOINING_OP filter_group',
        'filter_group JOINING_OP filter_group action_group',
    )
    def query(self, p):
        return p

    @_(
        'filter',
        'BRACE_OPEN filter { JOINING_OP filter } BRACE_CLOSE'
    )
    def filter_group(self, p):
        return p

    @_(
        'KEY COMP_OP value',
        'KEY COMP_OP array',
    )
    def filter(self, p):
        return p

    @_(
        'STRING',
        'NUMBER',
        'TIME',
        'DATE',
        'DATETIME'
    )
    def value(self, p):
        return p

    @_(
        'SQUARE_OPEN value { COMMA value } SQUARE_CLOSE',
        'SQUARE_OPEN SQUARE_CLOSE'
    )
    def array(self, p):
        return p

    @_(
        'action',
        'action action'
    )
    def action_group(self, p):
        return p

    @_(
        'PIPE ACTION_KEY KEY { value }',
        'PIPE ACTION_KEY value { value }',
    )
    def action(self, p):
        return p

    # @_('SORT_BY KEY',
    #    'SORT_BY KEY KEY')
    # def sort(self, p):
    #     if len(p) == 2:
    #         order = 'asc'
    #     else:
    #         if p[2].startswith('a'):
    #             order = 'asc'
    #         else:
    #             order = 'desc'
    #     return SimpleQueryParser.QuerySortBy(by_key=p[1], order=order)
    #
    # @_('KEY COMP_OP VALUE')
    # def expr(self, p):
    #     converted_value = SydParser.covert_one_value(p[2])
    #     return SimpleQueryParser.QuerySection(key=p[0], comp_op=p[1], value=converted_value)
    #
    # @_('expr OR expr',
    #    'expr AND expr')
    # def expr(self, p):
    #     left_section, right_section = p[0], p[2]
    #     return CmpQueryNode(p[1], left_section, right_section)

    # def error(self, p):
    #     text = self.__text
    #     if not p:
    #         text_rest = ''
    #         err_txt = generate_error_message(text, text_rest)
    #         err = SynamicQueryParsingError(
    #             f'End of query string before tokens could be parsed sensibly.\nDetails:{err_txt}'
    #         )
    #     else:
    #         text_rest = self.__text[p.index:]
    #         err_txt = generate_error_message(text, text_rest)
    #         err = SynamicQueryParsingError(
    #             f'Parsing error at token {p.type}.\nDetails:{err_txt}'
    #         )
    #     raise err
