from expr import LambdaTerm, Abstraction, Application, Symbol, Variable, Opaque, make_chnum

class InvalidMonadException(Exception):
    def __init__(self, evaled):
        super(InvalidMonadException, self).__init__()
        self.evaled = evaled

class MonadIOAction:
    def __init__(self, name, arg_names, run):
        self.symb = Symbol(name)
        self.arg_names = arg_names
        self.run = run

    def n_args(self):
        return len(self.arg_names)

    # Returns None if term does not match against self.symb/self.n_args
    # Returns the arguments if it matches
    def match_against(self, term):
        arg_list = []
        for i in range(self.n_args()):
            if isinstance(term, Application):
                arg_list.append(term.callee)
                term = term.caller
            else:
                return None
        if term != self.symb:
            return None

        return arg_list[::-1] # Outermost argument last

    def to_json_obj(self):
        return {
            "symb": self.symb.name,
            "arg_names": self.arg_names,
        }

    def __str__(self):
        return f"MonadIOAction(symb={self.symb}, arg_names={self.arg_names})"

    __repr__ = __str__

class BindAction(MonadIOAction):
    def __init__(self):
        super(BindAction, self).__init__("bind", ["io", "iofn"], None)

class MonadIOLayout:
    def __init__(self, actions):
        self.actions = actions
        self.actions.append(BindAction())

    def apply_monad(self, monad):
        for action in self.actions:
            monad = Application(monad, action.symb)

        return monad

    def match_monad_result(self, monad_result):
        for action in self.actions:
            args = action.match_against(monad_result)
            if args is not None:
                return action, args

    def constructor_for_idx(self, i):
        # λa0 ... an. c0 ... cm. ci a0 ... an

        action = self.actions[i]
        print("Constructor for", action.symb)

        result = Variable(action.symb.name)
        for arg in action.arg_names:
            result = Application(result, Variable(arg))

        for other_action in self.actions[::-1]:
            result = Abstraction(other_action.symb.name, result)

        for arg in action.arg_names[::-1]:
            result = Abstraction(arg, result)

        result = Opaque(action.symb.name, result)

        return result

    def to_json_obj(self):
        return {
            "actions": [action.to_json_obj() for action in self.actions],
        }

# kwargs are passed into the inner action functions
def eval_monad_io(layout, term, **kwargs):
    monad_res = layout.apply_monad(term).whnf(force_opaques=True)

    matched = layout.match_monad_result(monad_res)
    print(matched)

    if matched is None:
        raise InvalidMonadException(matched)
    else:
        action, args = matched

        if isinstance(action, BindAction):
            # Special! y >>= x
            y_res = eval_monad_io(layout, args[0], **kwargs).whnf()
            x_applied = Application(args[1], y_res)
            return eval_monad_io(layout, x_applied, **kwargs).whnf()

        res = action.run(*args, **kwargs)
        return res

def _make_standard_io_layout():
    def mpure(x):
        return x

    def mprint(x):
        print("Monadic print:", x)
        return Abstraction("x", Variable("x"))

    def mread():
        inp = int(input("Monadic read number: "))
        return make_chnum(inp)

    def mxyz(x, y, z):
        print(f"x = {x}, y = {y}, z = {z}")
        return Abstraction("x", Variable("x"))

    console_io = MonadIOLayout([
        MonadIOAction("pure", ["x"], mpure),
        MonadIOAction("print", ["out"], mprint),
        MonadIOAction("read", [], mread),
        MonadIOAction("xyz", ["x", "y", "z"], mxyz),
    ])

    return console_io

CONSOLE_IO = _make_standard_io_layout()

CONSOLE_EIO = lambda term: eval_monad_io(CONSOLE_IO, term)

if __name__ == "__main__":
    from expr import *

    λ = multi_lambda
    C = multi_apply
    V = Variable

    c_pure, c_print, c_read, c_xyz, c_bind = [CONSOLE_IO.constructor_for_idx(i) for i in range(5)]

    print(c_xyz)

    program = C(
        c_bind,
        c_read,
        λ("a",
            C(
                c_bind,
                c_read,
                λ("b",
                    C(
                        c_bind,
                        c_read,
                        λ("c",
                            C(
                                c_xyz,
                                Variable("a"),
                                Variable("b"),
                                Variable("c"),
                            )
                        )
                    )
                )
            )
        )
    )

    print(program)
    print(CONSOLE_EIO(program))

    print(CONSOLE_IO.constructor_for_idx(3))
