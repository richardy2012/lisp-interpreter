from printer import pr_str
import mal_types

def prn(obj):
    print(pr_str(obj, print_readably=True))
    return mal_types.MalNil()

ns = {
    '+': lambda a, b: mal_types.MalNumber(a.data + b.data), # fixme: operate and return maltypes directly
    '-': lambda a, b: mal_types.MalNumber(a.data - b.data),
    '*': lambda a, b: mal_types.MalNumber(a.data * b.data),
    '/': lambda a, b: mal_types.MalNumber((a.data / b.data)),
    "prn": prn,
    "list": lambda *x: mal_types.MalList(x),
    "list?": lambda x: mal_types.MalBool(True if isinstance(x, mal_types.MalList) else False),
    "empty?": lambda x: mal_types.MalBool(len(x) == 0),
    "count": lambda x: mal_types.MalNumber(len(x)),
    "=": lambda x,y: mal_types.MalBool(x.data==y.data),
    "<": lambda x, y: mal_types.MalBool(x.data<y.data),
    "<=": lambda x,y: mal_types.MalBool(x.data<=y.data),
    ">": lambda x,y: mal_types.MalBool(x.data>y.data),
    ">=": lambda x,y: mal_types.MalBool(x.data>=y.data),
}