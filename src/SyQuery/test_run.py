from SyQuery.parser.parser import SyQueryParser
from pprint import pprint

text = """(time == 12:20 and name == "Sabuj") or list == [7, "yes" , 77] | :sortby name 70; :limit 40"""
# text = " "
text = "n=='i'\r\n\n more > error"

sy_parser = SyQueryParser(text)
res = sy_parser.parse()
pprint(res, indent=2)
