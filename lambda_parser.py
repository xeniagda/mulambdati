from expr import *

class NoParse(Exception):
    pass

def mparse_map(f, parser):
    def parse_map(inp):
        data, inp = parser(inp)

        return f(data), inp

    return parse_map

def mparse_any(*parsers):
    def parse_any(inp):
        for parser in parsers:
            try:
                return parser(inp)
            except NoParse:
                continue
        raise NoParse

    return parse_any

def mparse_pred0(pred):
    def parse_pred0(inp):
        if len(inp) > 0 and pred(inp[0]):
            return inp[0], inp[1:]
        raise NoParse

    return parse_pred0

def mparse_many(parser, n=0):
    def parse_many(inp):
        parses = []
        while True:
            try:
                res, inp = parser(inp)
                parses.append(res)
            except NoParse:
                break
        if len(parses) < n:
            raise NoParse

        return parses, inp

    return parse_many

def mparse_seqlast(*parsers):
    def parse_seqlast(inp):
        val = None
        for parser in parsers:
            val, inp = parser(inp)
        return val, inp

    return parse_seqlast

def mparse_exact(text):
    def parse_exact(inp):
        if len(inp) >= len(text) and inp[:len(text)] == text:
            return text, inp[len(text):]

        raise NoParse

    return parse_exact

def mparse_parens(parser):
    def parse_parens(inp):
        _, inp = mparse_seqlast(parse_space, mparse_exact("("), parse_space)(inp)
        data, inp = parser(inp)
        _, inp = mparse_seqlast(parse_space, mparse_exact(")"), parse_space)(inp)

        return data, inp

    return parse_parens

parse_space = mparse_many(mparse_pred0(lambda x: x in " \n"))

def mparse_spaced(parser):
    def parse_spaced(inp):
        _, inp = parse_space(inp)
        data, inp = parser(inp)
        _, inp = parse_space(inp)

        return data, inp

    return parse_spaced


def parse_abstraction(inp):
    _, inp = mparse_spaced(mparse_any(mparse_exact("λ"), mparse_exact("\\")))(inp)

    r_variables, inp = mparse_many(mparse_spaced(parse_rawvar))(inp)

    _, inp = mparse_spaced(mparse_exact("."))(inp)

    term, inp = parse_term(inp)

    return multi_lambda(*r_variables, term), inp

parse_rawvar = mparse_map(
    "".join,
    mparse_many(mparse_pred0(lambda x: x in "abcdefghijklmnopqrstuvwxyz_0123456789"), n=1)
)

parse_variable = mparse_map(
    Variable,
    parse_rawvar
)

parse_symbol = mparse_map(
    Symbol,
    mparse_seqlast(mparse_exact("'"), parse_rawvar)
)


def parse_application(inp):
    call, inp = mparse_many(parse_term_small, n=2)(inp)

    return multi_apply(*call), inp

def parse_evalio(inp):
    _, inp = mparse_spaced(mparse_exact("%evalIO"))(inp)

    term, inp = parse_term(inp)

    return EvalIO(term), inp

def parse_term_small(inp):
    return mparse_any(
        mparse_parens(parse_term),
        mparse_spaced(mparse_any(parse_abstraction, parse_variable, parse_symbol, parse_evalio, mparse_parens(parse_application)))
    )(inp)

parse_term = mparse_any(parse_application, parse_term_small, parse_evalio)

def preproc(code):
    in_comment = False

    out = ""
    for ch in code:
        if in_comment and ch == "\n":
            in_comment = False
        if ch == "#":
            in_comment = True
        if not in_comment:
            out += ch
    return out

assert(
    parse_term("(λn f x. f (n f x)) (λf x. f (f (f x)))")[0]
    ==
    Application(
        multi_lambda(
            "n", "f", "x",
            Application(
                Variable("f"),
                multi_apply(Variable("n"), Variable("f"), Variable("x"))
            )
        ),
        multi_lambda(
            "f", "x",
            Application(
                Variable("f"),
                Application(
                    Variable("f"),
                    Application(
                        Variable("f"),
                        Variable("x"),
                    )
                )
            )
        )
    )
)

code = open("code.lmb", "r")
program = parse_term(preproc(code.read()))[0]

print(program.term.whnf().beta_reduce_once().whnf().beta_reduce_once())
print(program.whnf())
