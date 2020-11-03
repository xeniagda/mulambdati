from expr import *

class NoParse(Exception):
    def __init__(self, msg, len_left):
        self.msg = msg
        self.len_left = len_left

def mparse_map(f, parser):
    def parse_map(inp):
        data, inp = parser(inp)

        return f(data), inp

    return parse_map

def mparse_any(*parsers):
    def parse_any(inp):
        longest_error = None
        for parser in parsers:
            try:
                return parser(inp)
            except NoParse as e:
                if longest_error == None or e.len_left <= longest_error.len_left:
                    longest_error = e

        raise longest_error

    return parse_any

def mparse_pred0(pred, msg):
    def parse_pred0(inp):
        if len(inp) > 0 and pred(inp[0]):
            return inp[0], inp[1:]
        raise NoParse(msg, len(inp))

    return parse_pred0

def parse_eof(inp):
    if len(inp) == 0:
        return None, ""

    raise NoParse("Expected EOF", len(inp))

def mparse_eofed(parser):
    def parse_eofed(inp):
        data, inp = parser(inp)
        _, inp = parse_eof(inp)
        return data, inp

    return parse_eofed

def mparse_err(parser, msg):
    def parse_err(inp):
        try:
            return parser(inp)
        except NoParse as e:
            raise NoParse(msg, e.len_left)

    return parse_err

def mparse_ctx(parser, ctx_msg):
    def parse_ctx(inp):
        try:
            return parser(inp)
        except NoParse as e:
            raise NoParse(f"In {ctx_msg}: {e.msg}", e.len_left)

    return parse_ctx

def an_ctx(msg):
    return lambda parser: mparse_ctx(parser, msg)

def mparse_many(parser, n=0):
    def parse_many(inp):
        parses = []
        while True:
            try:
                res, inp = parser(inp)
                parses.append(res)
            except NoParse as e:
                if len(parses) < n:
                    raise NoParse(f"Needs {n - len(parses)} more. Inner: {e.msg}", e.len_left)

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

        raise NoParse(f"Expected {text}", len(inp))

    return parse_exact

def mparse_parens(parser):
    def parse_parens(inp):
        _, inp = mparse_seqlast(parse_space, mparse_exact("("), parse_space)(inp)
        data, inp = parser(inp)
        _, inp = mparse_seqlast(parse_space, mparse_exact(")"), parse_space)(inp)

        return data, inp

    return parse_parens

parse_space = mparse_many(mparse_pred0(lambda x: x in " \n", "Expected space"))

def mparse_spaced(parser):
    def parse_spaced(inp):
        _, inp = parse_space(inp)
        data, inp = parser(inp)
        _, inp = parse_space(inp)

        return data, inp

    return parse_spaced

@an_ctx("abstraction")
def parse_abstraction(inp):
    _, inp = mparse_spaced(mparse_any(mparse_exact("λ"), mparse_exact("\\")))(inp)

    r_variables, inp = mparse_many(mparse_spaced(parse_rawvar))(inp)

    _, inp = mparse_spaced(mparse_exact("."))(inp)

    term, inp = parse_term(inp)

    return multi_lambda(*r_variables, term), inp

parse_rawvar = mparse_map(
    "".join,
    mparse_many(mparse_pred0(lambda x: x in "abcdefghijklmnopqrstuvwxyz_0123456789", "Expected alnum"), n=1)
)

parse_variable = mparse_ctx(
    mparse_map(
        Variable,
        parse_rawvar
    ),
    "variable"
)

parse_symbol = mparse_ctx(
    mparse_map(
        Symbol,
        mparse_seqlast(mparse_exact("'"), parse_rawvar)
    ),
    "symbol"
)


@an_ctx("application")
def parse_application(inp):
    call, inp = mparse_many(parse_term_small, n=2)(inp)

    return multi_apply(*call), inp

@an_ctx("evalio")
def parse_evalio(inp):
    _, inp = mparse_spaced(mparse_exact("%evalIO"))(inp)

    term, inp = parse_term(inp)

    return EvalIO(term), inp

def parse_term_small(inp):
    return mparse_any(
        mparse_parens(parse_term),
        mparse_spaced(mparse_any(
            parse_abstraction,
            parse_variable,
            parse_symbol,
            parse_evalio,
            mparse_parens(parse_application)
        ))
    )(inp)

parse_term = mparse_any(parse_application, parse_term_small)

parse_code = mparse_eofed(parse_term)

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

def print_error(inp, pos, msg):
    for i, line in enumerate(inp.split("\n")):
        if len(line) < pos:
            pos -= len(line) + 1
            continue

        print(str(i).ljust(3), line)
        print(">".ljust(3), "-" * (pos - 1) + "^")
        print("Error:", msg)
        break

if __name__ == "__main__":

    code = open("code.lmb", "r").read()
    try:
        parsed = parse_application(preproc(code))
    except NoParse as e:
        print_error(code, len(code) - e.len_left - 1, e.msg)
        exit()

    program = parsed[0]


    print(program.whnf().beta_reduce_once().whnf().beta_reduce_once())
    print(program.whnf())
