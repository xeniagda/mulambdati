from expr import LambdaTerm, Abstraction, Application, Symbol, Variable, make_chnum
from monad_io import MonadIOAction, MonadIOLayout
from player import Player
import asyncio
import traceback
from token_gen import make_random_token

import logging

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
    def __init__(self, game_identifier, players, layout):
        self.players = players

        self.layout = layout
        self.combinators = []

        self.game_identifier = game_identifier

    def add_combinator(self, price, name, term):
        self.combinators.append(Combinator(name, price, term))

    async def start_game(self):
        try:
            tasks = []
            tasks.append(self.mana_loop())
            tasks.extend([self.start_player(i) for i in range(len(self.players))])

            await asyncio.gather(*tasks)
        except Exception as e:
            traceback.print_exc()
            return

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
            logging.info(f"Player {self.players[player_idx].sec_token} doing {action}")

            price = action.get_price(self)
            if self.players[player_idx].mana < price:
                await self.players[player_idx].tell_msg(f'You need {price} mana for that')
                continue

            self.players[player_idx].mana -= price
            await action.run(self, player_idx)


            for player in self.players:
                await player.update_state(self)

    def to_json_obj(self):
        return {
            "game_identifier": self.game_identifier,
            "players": [player.to_json_obj() for player in self.players],
            "layout": self.layout.to_json_obj(),
            "combinators": [comb.to_json_obj() for comb in self.combinators],
        }

def make_standard_game(player1_const, player2_const):
    pl1_token = make_random_token()
    pl2_token = make_random_token()

    pl1 = player1_const(pl1_token, 10, 0)
    pl2 = player2_const(pl2_token, 10, 0)

    Identity = lambda: Abstraction("x", Variable("x"))

    def pure(x, *, game, player_idx):
        return x

    action_pure = MonadIOAction("pure", ['x'], pure)

    def give_mana(*, game, player_idx):
        tok = game.players[player_idx].sec_token
        logging.info(f"Player {tok} gained 10 mana!")
        game.players[player_idx].mana += 10
        return Identity()

    action_give_mana = MonadIOAction("give_10_mana", [], give_mana)

    def do_damage(x, *, game, player_idx):
        tok = game.players[player_idx].sec_token
        otok = game.players[~player_idx].sec_token
        logging.info(f"Player {tok} dealt {x.name} damage to {otok}!")
        if type(x.name) == int:
            game.players[~player_idx].health -= x.name
        else:
            logging.info(f"Invalid type!")
            # await self.players[player_idx].tell_msg(f"do_damage needs an int, you gave {type(x.name)}")

        return Identity()

    action_do_damage = MonadIOAction("do_damage", ['x'], do_damage)

    def get_opponent_health(*, game, player_idx):
        tok = game.players[player_idx].sec_token
        logging.info(f"Player {tok} gets opponents health!")
        return Symbol(game.players[~player_idx].health)

    action_goh = MonadIOAction("get_opponent_health", [], get_opponent_health)

    layout = MonadIOLayout([action_pure, action_give_mana, action_do_damage, action_goh])

    game = Game(
        make_random_token(),
        [pl1, pl2],
        layout,
    )

    game.add_combinator(1, "pure", game.layout.constructor_for_idx(0))
    game.add_combinator(5, "+10 mana", game.layout.constructor_for_idx(1))
    game.add_combinator(10, "λx. do x damage", game.layout.constructor_for_idx(2))
    game.add_combinator(10, "get opponent's health", game.layout.constructor_for_idx(3))
    game.add_combinator(1, "bind", game.layout.constructor_for_idx(4))
    game.add_combinator(2, "the number 2", Symbol(2))
    game.add_combinator(7, "the number 7", Symbol(7))

    return game, pl1_token, pl2_token
