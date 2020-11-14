from expr import LambdaTerm, Abstraction, Application, Symbol, Variable, make_chnum
from player import Player
import asyncio

class Game:
    def __init__(self, players, layout_const):
        self.players = players
        self.turn = 0 # indexes players

        self.layout = layout_const(self)
        self.combinators = []

    def add_combinator(self, price, name, term):
        self.combinators.append((price, name, term))

    async def do_turn(self):
        await asyncio.gather(*[pl.update_state(self) for pl in self.players])

        action = await self.players[self.turn].get_action()

        action.run(self)
        self.turn = (self.turn + 1) % len(self.players)

