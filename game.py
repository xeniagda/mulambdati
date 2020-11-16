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

    async def start_game(self):
        tasks = []
        tasks.append(self.mana_loop())
        tasks.extend([self.start_player(i) for i in range(len(self.players))])

        await asyncio.gather(*tasks)

    async def mana_loop(self):
        while True:
            await asyncio.sleep(1)
            for pl in self.players:
                pl.mana += 1
                await pl.update_state(self)

    async def start_player(self, player_idx):
        await self.players[player_idx].update_state(self)
        while True:
            action = await self.players[player_idx].get_action()

            action.run(self, player_idx)
            for player in self.players:
                await player.update_state(self)


