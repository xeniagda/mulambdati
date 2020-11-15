from abc import ABC, abstractmethod

letters = "abcdefghijklmnopqrstuvwxyz"
def n_to_base(n, base):
    if n < len(base):
        return base[n]

    return n_to_base(n // len(base)) + base[n % len(base)]

def make_new_name(name, took_names):
    n = 0
    while True:
        new_name = name + "_" + n_to_base(n, letters)
        if new_name not in took_names:
            return new_name
        n += 1

class StringifyMode:
    def __init__(self):
        pass

    def combine_lambdas(self):
        return True

    def call_with_prefix(self):
        return False

    def term_length_for_parens(self):
        return 30 # Only applicable when call_with_parens == False

    def lambda_sign(self):
        return "λ"

    def prefix_sign(self):
        return "`"

    def expand_opaques(self):
        return False

# Precedence:
#   λa. b = 1
#   a b = 0

class LambdaTerm(ABC):
    @abstractmethod
    def stringify(self, mode, prec):
        pass

    @abstractmethod
    def free_variables(self):
        pass

    @abstractmethod
    def replace(self, name, term):
        pass

    def beta_reduce_once(self):
        return self.beta_reduce()

    @abstractmethod
    def beta_reduce(self):
        pass

    @abstractmethod
    def whnf(self, force_opaques=False):
        pass

    @abstractmethod
    def __eq__(self):
        pass

    def __str__(self):
        return self.stringify(StringifyMode(), 10)

    def __repr__(self):
        return self.stringify(StringifyMode(), 10)

class Abstraction(LambdaTerm): # λv. t
    def __init__(self, variable, term):
        super(Abstraction, self).__init__()
        self.variable = variable
        self.term = term

    def __eq__(self, other):
        if isinstance(other, Abstraction):
            return self.variable == other.variable and self.term == other.term
        return False

    def stringify(self, mode, prec):
        if mode.combine_lambdas:
            variable_list = []
            current_term = self

            while isinstance(current_term, Abstraction):
                variable_list.append(current_term.variable)
                current_term = current_term.term

            res = mode.lambda_sign() + " ".join(variable_list) + ". " + current_term.stringify(mode, 1)
        else:
            res = mode.lambda_sign() + self.variable + ". " + self.term.stringify(mode, 1)

        if prec < 1:
            return "(" + res + ")"
        else:
            return res

    def free_variables(self):
        return self.term.free_variables() - set(self.variable)

    def replace(self, name, term):
        if self.variable == name:
            return self
        else:
            var = self.variable
            sterm = self.term
            if self.variable in term.free_variables():
                var = make_new_name(self.variable, term.free_variables())
                sterm = sterm.replace(self.variable, Variable(var))

            return Abstraction(var, sterm.replace(name, term))

    def beta_reduce_once(self):
        return Abstraction(self.variable, self.term.beta_reduce_once())

    def beta_reduce(self):
        return Abstraction(self.variable, self.term.beta_reduce())

    def whnf(self, force_opaques=False):
        return self

class Variable(LambdaTerm): # v
    def __init__(self, variable):
        super(Variable, self).__init__()

        self.variable = variable

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.variable == other.variable
        return False

    def stringify(self, mode, prec):
        return self.variable

    def free_variables(self):
        return {self.variable}

    def replace(self, name, term):
        if name == self.variable:
            return term
        return self

    def beta_reduce(self):
        return self

    def whnf(self, force_opaques=False):
        return self

class Application(LambdaTerm): # t1 t2
    def __init__(self, caller, callee):
        super(Application, self).__init__()
        self.caller = caller
        self.callee = callee

    def __eq__(self, other):
        if isinstance(other, Application):
            return self.caller == other.caller and self.callee == other.callee
        return False

    def stringify(self, mode, prec):
        if mode.call_with_prefix():
            res = mode.prefix_sign() + self.caller.stringify(mode, prec) + self.callee.stringify(mode, prec)
            if len(res) > mode.term_length_for_parens():
                res = "(" + res + ")"
        else:
            res = self.caller.stringify(mode, 0) + " " + self.callee.stringify(mode, -1)

            if prec < 0:
                res = "(" + res + ")"
        return res

    def free_variables(self):
        return self.caller.free_variables() | self.callee.free_variables()

    def replace(self, name, term):
        return Application(self.caller.replace(name, term), self.callee.replace(name, term))

    def beta_reduce_once(self):
        caller = self.caller.beta_reduce_once()
        callee = self.callee.beta_reduce_once()

        if isinstance(caller, Abstraction):
            return caller.term.replace(caller.variable, callee)

        return Application(caller, callee)

    def beta_reduce(self):
        caller = self.caller.beta_reduce()
        callee = self.callee.beta_reduce()

        if isinstance(caller, Abstraction):
            return caller.term.replace(caller.variable, callee).beta_reduce()

        return Application(caller, callee)

    def whnf(self, force_opaques=False):
        caller = self.caller.whnf(force_opaques)

        if isinstance(caller, Abstraction):
            return caller.term.replace(caller.variable, self.callee).whnf(force_opaques)

        return Application(caller, self.callee)


I = Abstraction("x", Variable("x"))

def multi_apply(fun, *args):
    if len(args) == 0:
        return fun
    return Application(multi_apply(fun, *args[:-1]), args[-1])

def multi_lambda(*args):
    if len(args) == 1:
        return args[0]

    return Abstraction(args[0], multi_lambda(*args[1:]))

class Symbol(LambdaTerm): # %evalIO a b
    def __init__(self, symbol):
        super(Symbol, self).__init__()
        self.name = symbol

    def stringify(self, mode, prec):
        if isinstance(self.name, str):
            return "'" + self.name
        else:
            return type(self.name).__name__ + "'" + str(self.name)

    def free_variables(self):
        return set()

    def replace(self, name, term):
        return self

    def beta_reduce(self):
        return self

    def whnf(self, force_opaques=False):
        return self

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return other.name == self.name
        return False

class Opaque(LambdaTerm):
    def __init__(self, name, term):
        super(Opaque, self).__init__()
        self.name = name
        self.term = term

    def stringify(self, mode, prec):
        if mode.expand_opaques():
            return self.term.stringify(mode, prec)
        return f"#{self.name}"

    def free_variables(self):
        return self.term.free_variables()

    def replace(self, name, term):
        after = self.term.replace(name, term)
        if self.term == after:
            return self
        return after

    def beta_reduce(self):
        after = self.term.beta_reduce()
        if self.term == after:
            return self
        return after

    def whnf(self, force_opaques=False):
        after = self.term.whnf()
        if self.term == after and not force_opaques:
            return self
        return after

    def __eq__(self, other):
        if isinstance(other, Opaque):
            return other.name == self.name and self.term == other.term
        return False

def make_chnum_term(n):
    if n == 0:
        return Variable("x")
    return Application(Variable("f"), make_chnum_term(n - 1))

def make_chnum(n):
    return Abstraction("f", Abstraction("x", make_chnum_term(n)))

def unpack_chnum(n):
    n = Application(Application(n, Symbol("f")), Symbol("x")).beta_reduce()

    i = 0
    while True:
        if isinstance(n, Application) and n.caller == Symbol("f"):
            i += 1
            n = n.callee
        elif n == Symbol("x"):
            return i
        else:
            return None

