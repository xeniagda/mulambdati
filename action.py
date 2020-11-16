from expr import Application, Variable, Abstraction
from abc import ABC, abstractmethod
from monad_io import eval_monad_io

class Action(ABC):
    def __init__(self, combinators, fvs, abstractions, deck_combine, eval_terms):
        self.combinators = combinators
        self.fvs = fvs # [str]
        self.abstractions = abstractions # [(int, str)]
        self.deck_combine = deck_combine
        self.eval_terms = eval_terms

    @abstractmethod
    def get_price(self, game):
        pass

    @abstractmethod
    async def run(self, game, player_idx):
        pass

class PurchaseCombinator(Action):
    def __init__(self, combinator_idx):
        self.combinator_idx = combinator_idx

    def get_price(self, game):
        return game.combinators[self.combinator_idx].price

    async def run(self, game, player_idx):
        player = game.players[player_idx]

        comb = game.combinators[self.combinator_idx]

        player.deck.append(comb.term)

class PurchaseFreeVariable(Action):
    def __init__(self, var_name):
        self.var_name = var_name

    def get_price(self, game):
        return 1

    async def run(self, game, player_idx):
        player = game.players[player_idx]

        player.deck.append(Variable(self.var_name))

class BindVariable(Action):
    def __init__(self, bind_name, deck_idx):
        self.bind_name = bind_name
        self.deck_idx = deck_idx

    def get_price(self, game):
        return 1

    async def run(self, game, player_idx):
        player = game.players[player_idx]

        player.deck[self.deck_idx] = Abstraction(self.bind_name, player.deck[self.deck_idx])

class Apply(Action):
    def __init__(self, caller_idx, callee_idx):
        self.caller_idx = caller_idx
        self.callee_idx = callee_idx

    def get_price(self, game):
        return 0

    async def run(self, game, player_idx):
        player = game.players[player_idx]

        if self.caller_idx == self.callee_idx:
            await player.tell_msg("Caller and callee must be different!")
            return

        player.deck[self.caller_idx] = Application(
            player.deck[self.caller_idx],
            player.deck[self.callee_idx]
        ).whnf()

        del player.deck[self.callee_idx]

class Eval(Action):
    def __init__(self, deck_idx):
        self.deck_idx = deck_idx

    def get_price(self, game):
        return 2

    async def run(self, game, player_idx):
        player = game.players[player_idx]

        term = eval_monad_io(game.layout, player.deck[self.deck_idx])
        player.deck[self.deck_idx] = term.whnf()
