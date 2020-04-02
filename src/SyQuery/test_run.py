from SyQuery.parser.parser import QueryLexer, QueryParser
from pprint import pprint

text = """(time == 12:20 and name == "Sabuj") or list == [7, "yes" , 77] | :sortby name 70; :limit 40"""

lexer = QueryLexer()
for token in lexer.tokenize(text):
    print(f"({token.type})  {token.value}")

parser = QueryParser(text)
res = parser.parse(lexer.tokenize(text))
pprint(res, indent=2)
