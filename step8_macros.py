import reader
import printer
import mal_types
from env import Env
from core import ns
import sys


repl_env = Env()
repl_env.set('eval', lambda ast: EVAL(ast, repl_env))
for k, v in ns.items():
    repl_env.set(k, v)


def is_pair(ast):
    if isinstance(ast, mal_types.list_types) and len(ast.data) > 0:
        return True
    return False


def quasiquote(ast):
    if not is_pair(ast):
        return mal_types.MalList([mal_types.MalSymbol('quote'), ast])
    elif ast[0].data == 'unquote':
        return ast[1]
    elif isinstance(ast[0], mal_types.list_types) and \
            isinstance(ast[0][0], mal_types.MalSymbol) and \
            ast[0][0].data == 'splice-unquote':
        return mal_types.MalList([mal_types.MalSymbol('concat'), ast[0][1], quasiquote(ast[1:])])
    else:
        return mal_types.MalList([mal_types.MalSymbol('cons'), quasiquote(ast[0]), quasiquote(ast[1:])])



def is_macro_call(ast, env):
    if isinstance(ast, mal_types.MalList) and isinstance(ast[0], mal_types.MalSymbol):
        try:
            f = env.get(ast[0])
        except mal_types.MalException:
            f = None
        if isinstance(f, mal_types.MalFn) and f.is_macro:
            return True
    return False


def macroexpand(ast, env):
    while is_macro_call(ast, env):
        f = env.get(ast[0])
        ast = f(*ast[1:])
    return ast

def READ(string):
    return reader.read_str(string)


def EVAL(ast, env):
    while True:
        if not isinstance(ast, mal_types.list_types):
            return eval_ast(ast, env)
        elif not ast:
            return ast
        elif isinstance(ast, mal_types.list_types):
            if len(ast) == 0:
                return ast
            ast = macroexpand(ast, env)
            if not isinstance(ast, mal_types.list_types):
                return eval_ast(ast, env)
            if isinstance(ast[0], mal_types.MalSymbol):
                if ast[0].data == 'macroexpand':
                    return macroexpand(ast[1], env)

                if ast[0].data == 'def!':
                    value = EVAL(ast[2], env)
                    env.set(ast[1].data, value)
                    return value

                elif ast[0].data == 'defmacro!':
                    value = EVAL(ast[2], env)
                    value.is_macro = True
                    env.set(ast[1].data, value)
                    return value

                elif  ast[0].data == 'let*':
                    let_env = Env(outer=env)
                    for k ,v in  zip(ast[1][::2], ast[1][1::2]):
                        let_env.set(k, EVAL(v, let_env))
                    ast, env = ast[2], let_env
                    continue

                elif ast[0].data == 'do':
                    ast = eval_ast(ast[1:], env)[-1]
                    return ast

                elif ast[0].data == 'if':
                    if EVAL(ast[1], env):
                        ast = ast[2]
                        continue
                    else:
                        if len(ast) == 4:
                            ast = ast[3]
                            continue
                        return mal_types.MalNil()

                elif ast[0].data == 'fn*':
                    def fn(*exprs):
                        new_env = Env(outer=env, binds=ast[1], exprs=exprs)
                        return EVAL(ast[2], new_env)
                    return mal_types.MalFn(ast=ast[2], params=ast[1], env=env, fn=fn)

                elif ast[0].data == 'quote':
                    return ast[1]

                elif ast[0].data == 'quasiquote':
                    ast = quasiquote(ast[1])
                    continue

            # apply
            evaluated_ast = eval_ast(ast, env)
            if callable(evaluated_ast[0]):
                f, args = evaluated_ast[0], evaluated_ast[1:]
                if isinstance(f, mal_types.MalFn):
                    ast= f.ast
                    env = Env(outer=f.env, binds=f.params, exprs=args)
                    # print(f)
                    continue
                else:
                    return f(*args)
            return evaluated_ast
        return mal_types.MalNil()


def eval_ast(ast, env):
    if isinstance(ast, mal_types.MalSymbol):
        v = env.get(ast)
        if v is None:
            raise mal_types.MalException("'{}' not found.".format(ast.data))
        return v
    elif isinstance(ast, mal_types.list_types):
        class_type = ast.__class__
        return class_type([EVAL(i, env) for i in ast])
    elif isinstance(ast, mal_types.MalHashMap):
        return mal_types.MalHashMap({EVAL(k, env): EVAL(v, env) for k, v in ast.items()})
    return ast

def PRINT(ast):
    return printer.pr_str(ast)


def rep(input):
    return PRINT(EVAL(READ(input), repl_env))


def main():
    rep("(def! not (fn* (a) (if a false true)))")
    rep('(def! load-file (fn* (f) (eval (read-string (str "(do " (slurp f) ")")))))')
    rep("""(defmacro! cond (fn* (& xs) (if (> (count xs) 0) (list'if (first xs) (if (> (count xs) 1) (nth xs 1) (throw "odd number of forms to cond")) (cons'cond (rest (rest xs)))))))""")
    rep("""(defmacro! or (fn* (& xs) (if (empty? xs) nil (if (= 1 (count xs)) (first xs) `(let* (or_FIXME ~(first xs)) (if or_FIXME or_FIXME (or ~@(rest xs))))))))""")
    repl_env.set("*ARGV*", mal_types.MalList([mal_types.MalString(i) for i in sys.argv[2:]]))
    if sys.argv[1:]:
        rep('(load-file "{}")'.format(sys.argv[1]))
        exit()
    while True:
        try:
            print(rep(input("user> ")))
        except mal_types.MalException as e:
            # raise e
            print(e)
        except Exception as e:
            # raise e
            print(e)

if __name__ == '__main__':
    main()