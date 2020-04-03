from SyQuery.parser.parser import QueryLexer, QueryParser
from pprint import pprint

text = """(time == 12:20 and name == "Sabuj") or list == [7, "yes" , 77] | :sortby name 70; :limit 40"""
# text = " "
text = "n=='i'\r\n\n more > error"

lexer = QueryLexer()
# for token in lexer.tokenize(text):
#     print(f"({token.type})  {token.value}")

parser = QueryParser(text)
tokens = lexer.tokenize(text)
res = parser.parse(tokens)
pprint(res, indent=2)
