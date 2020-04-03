import re
from sly import Lexer, Parser
from SyQuery.exceptions import SynamicQueryParsingError
from .nodes import FilterNode, JoinerNode, ActionNode, Query


def generate_error_message(text, text_rest):
    # TODO: for multiline query error
    err_before_txt = '_' * (len(text) - len(text_rest))
    err_after_txt = '^' * len(text_rest)
    err_txt = '\n' + text + '\n' + err_before_txt + err_after_txt
    return err_txt


class SyQueryParser:
    def __init__(self, text):
        self.__text = text

    def parse(self):
        """
        (title == something or type in ["go", "yes"]) and age > 6
        """
        # TODO: generate detailed error message with annotations and (line, index) tracking
        text = self.__text
        lexer = LexQueryLexer()
        parser = YaccQueryParser()
        tokens = lexer.tokenize(text)
        res = parser.parse(tokens)
        return res


class LexQueryLexer(Lexer):
    tokens = {'KEY', 'ACTION_KEY', 'COMP_OP', 'STRING', 'NUMBER', 'TIME', 'DATE', 'DATETIME', 'JOINING_OP', 'BRACE_OPEN', 'BRACE_CLOSE', 'COMMA', 'SQUARE_OPEN', 'SQUARE_CLOSE', 'PIPE', 'SEMICOLON'}

    @_(r'\r\n|\n|\r')
    def ignore_newline(self, t):
        self.lineno += 1

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
            t.value = t.value[1:-1].replace('\\', '')
        return t

    @_(r'[+-]?[0-9]+(\.[0-9]+)?')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r',')
    def COMMA(self, t):
        return t

    @_(
        ';'
    )
    def SEMICOLON(self, t):
        return t

    def error(self, t):
        err = SynamicQueryParsingError(
            f'''\
Lexing error starting @ 
Line no: {self.lineno}
Text: {t.value}.'''
        )
        raise err


class YaccQueryParser(Parser):
    # Get the token list from the lexer (required)
    tokens = {*LexQueryLexer.tokens, }
    precedence = [
        ('left', 'BRACE_OPEN'),
        # ('left', 'SQUARE_OPEN'),
        # ('left', 'COMP_OP'),
    ]

    # Grammar rules and actions
    @_(
        'filters',
        'actions',
        'filters actions'
    )
    def query(self, p):
        query_tree = Query()
        if len(p) == 1:
            if isinstance(p[0], FilterNode):
                query_tree.set_filter(p[0])
            else:
                query_tree.set_actions(p[0])
        else:
            query_tree.set_filter(p[0])
            query_tree.set_actions(p[1])
        return query_tree

    @_('')
    def query(self, p):
        return Query()

    @_(
        'filter_group { JOINING_OP filter_group }'
    )
    def filters(self, p):
        if len(p) == 1:
            p = [('INVALID', p[0])]
        else:
            p = [('INVALID', p[0]), *p[1]]
        count = 0
        prev_joiner_node = None
        for joining_op, current_joiner_node in p:
            count += 1
            if count != 1:
                # skip if this is the first one. we gotta attach to it's right next.
                prev_joiner_node.set_right(joining_op, current_joiner_node)
            prev_joiner_node = current_joiner_node
        return p[0][1]

    @_(
        'filter',
        'BRACE_OPEN filter { JOINING_OP filter } BRACE_CLOSE'
    )
    def filter_group(self, p):
        p = list(p)

        if len(p) == 1:
            p = [('INVALID', p[0])]
        else:
            p = [('INVALID', p[1]), *p[2]]  # skip open and closing braces and the first filter and expand inner array
        first_joiner_node = prev_joiner_node = JoinerNode()
        count = 0
        for joining_op, current_filter_node in p:
            count += 1
            _left_leaf_joiner_node = JoinerNode()
            _left_leaf_joiner_node.set_leaf(current_filter_node)
            if count == 1:  # first
                prev_joiner_node.set_left(_left_leaf_joiner_node)
            else:  # next ones
                _right_joiner_node = JoinerNode()
                _right_joiner_node.set_left(_left_leaf_joiner_node)
                prev_joiner_node.set_right(joining_op, _right_joiner_node)
                prev_joiner_node = _right_joiner_node
        if len(p) == 1:
            return first_joiner_node
        else:
            root_joiner_node = JoinerNode()
            root_joiner_node.set_left(first_joiner_node)
            return root_joiner_node

    @_(
        'KEY COMP_OP value',
        'KEY COMP_OP array',
    )
    def filter(self, p):
        return FilterNode(p[0], p[1], p[2])

    @_(
        'STRING',
        'NUMBER',
        'TIME',
        'DATE',
        'DATETIME'
    )
    def value(self, p):
        return p[0]

    @_(
        'SQUARE_OPEN value { COMMA value } SQUARE_CLOSE',
        'SQUARE_OPEN SQUARE_CLOSE'
    )
    def array(self, p):
        elements = []
        p = list(p)[1:-1]
        if p:
            elements.append(p[0])
            if len(p) > 1:
                for comma, value in p[1]:
                    elements.append(value)
        return elements

    @_(
        'PIPE action { SEMICOLON action }'
    )
    def actions(self, p):
        p = [p[1], *list(map(lambda x: x[1], p[2]))]
        return p

    @_(
        'ACTION_KEY KEY { KEY }',
        'ACTION_KEY KEY { value }',
        'ACTION_KEY value { value }',
    )
    def action(self, p):
        action_key = p[0]
        action_params = [p[1], *p[2]]
        return ActionNode(action_key, action_params)

    def error(self, p):
        if not p:
            err = SynamicQueryParsingError(
                f'End of query string before tokens could be parsed sensibly.'
            )
        else:
            err = SynamicQueryParsingError(
                f'''Parsing error @
                Token: {p.type}.
                Line No: {p.lineno}'''
            )
        raise err
