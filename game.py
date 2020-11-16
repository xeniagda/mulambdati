from expr import LambdaTerm, Abstraction, Application, Symbol, Variable, make_chnum
from monad_io import MonadIOAction, MonadIOLayout
from player import Player
import asyncio

class Combinator:
    def __init__(self, name, price, term):
        self.name = name
        self.price = price
        self.term = term

    def to_json_obj(self):
        return {
            "name": self.name,
            "price": self.price,
            "term": self.term.to_json_obj(),
        }

class Game:
    def __init__(self, players, layout_const):
        self.players = players
        self.turn = 0 # indexes players

        self.layout = layout_const(self)
        self.combinators = []

    def add_combinator(self, price, name, term):
        self.combinators.append(Combinator(name, price, term))

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

    def to_json_obj(self):
        return {
            "players": [player.to_json_obj() for player in self.players],
            "layout": self.layout.to_json_obj(),
            "combinators": [comb.to_json_obj() for comb in self.combinators],
        }

def make_standard_game(player1_const, player2_const):
    pl1_token = make_random_token()
    pl2_token = make_random_token()

    pl1 = player1_const(pl1_token, 10, 0)
    pl2 = player2_const(pl2_token, 10, 0)

    def make_layout(game):
        Identity = Abstraction("x", Variable("x"))

        def pure(x):
            return x

        action_pure = MonadIOAction("pure", ['x'], pure)

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

        layout = MonadIOLayout([action_pure, action_give_mana, action_do_damage, action_goh])
        return layout

    game = Game(
        [pl1, pl2],
        make_layout,
    )

    game.add_combinator(1, "pure", game.layout.constructor_for_idx(0))
    game.add_combinator(5, "+10 mana", game.layout.constructor_for_idx(1))
    game.add_combinator(10, "λx. do x damage", game.layout.constructor_for_idx(2))
    game.add_combinator(10, "get opponent's health", game.layout.constructor_for_idx(3))
    game.add_combinator(1, "bind", game.layout.constructor_for_idx(4))
    game.add_combinator(2, "the number 2", Symbol(2))
    game.add_combinator(7, "the number 7", Symbol(7))

    return game, pl1_token, pl2_token
