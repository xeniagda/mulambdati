from expr import LambdaTerm, Abstraction, Application, Symbol, Variable, make_chnum
from monad_io import MonadIOAction, MonadIOLayout
from player import ConsolePlayer

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


if __name__ == "__main__":
    import sys
    tty1i, tty1o, tty2i, tty2o = sys.argv[1:5]
    with open(tty1i, "r") as it1, open(tty1o, "w") as ot1, open(tty2i, "r") as it2, open(tty2o, "w") as ot2:
        ot1.write("=== RESTART ===\n"); ot1.flush()
        ot2.write("=== RESTART ===\n"); ot2.flush()

        pl1 = ConsolePlayer(10, 0, it1, ot1)
        pl2 = ConsolePlayer(10, 0, it2, ot2)

        # Combinators:
        #   give_mana: +10 mana
        #   do_damage x: perform x damage
        #   get_opponent_health
        #   receive_expr: λx. you get the card x.
        #   sym_10: the number 10
        #   sym_2: the number 2

        def make_layout(game):
            Identity = Abstraction("x", Variable("x"))

            def give_mana():
                print(f"Player {game.turn} gained 10 mana!")
                game.players[game.turn].mana += 10
                return Identity

            action_give_mana = MonadIOAction("give_10_mana", [], give_mana)

            def do_damage(x):
                print(f"Player {game.turn} dealt {x.name} damage!")
                game.players[~game.turn].health -= x.name
                return Identity

            action_do_damage = MonadIOAction("do_damage", ['x'], do_damage)

            def get_opponent_health():
                print(f"Player {game.turn} gets opponents health!")
                return Symbol(game.players[~game.turn].health)

            action_goh = MonadIOAction("get_opponent_health", [], get_opponent_health)

            layout = MonadIOLayout([action_give_mana, action_do_damage, action_goh])
            return layout

        game = Game(
            [pl1, pl2],
            make_layout,
        )

        game.add_combinator(5, "+10 mana", game.layout.constructor_for_idx(0))
        game.add_combinator(10, "λx. do x damage", game.layout.constructor_for_idx(1))
        game.add_combinator(10, "get opponent's health", game.layout.constructor_for_idx(2))
        game.add_combinator(1, "bind", game.layout.constructor_for_idx(3))
        game.add_combinator(2, "the number 2", Symbol(2))
        game.add_combinator(7, "the number 7", Symbol(7))


        async def run():
            while True:
                await game.do_turn()

        asyncio.run(run())
