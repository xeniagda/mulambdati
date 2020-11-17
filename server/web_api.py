import asyncio
from aiohttp import web
from game import make_standard_game
from player import ExternalPlayer
import traceback
import json
from action import *

def make_json_response(data, status=200):
    return web.Response(
        body=json.dumps(data),
        content_type='application/json',
    )

def pl_fn(*, find_player, read_data, expects=None):
    if not read_data and expects is not None:
        raise ValueError("read_data = False, expects != None")
    def decorator(f):
        async def inner(self, req):
            if read_data:
                try:
                    data = await req.json()
                    for key in expects:
                        if key not in data:
                            return make_json_response({"expected": expects, "missing": key}, status=400)
                except Exception as e:
                    print("JSON decode error:", e)
                    return make_json_response({"error": "invalid json!"}, status=400)

            if find_player:
                if not 'sec_token' in req.cookies:
                    return make_json_response({"error": "sec_token required"}, status=400)

                idx_game = self.get_state_for_player(req.cookies['sec_token'])
                if idx_game is None:
                    resp = make_json_response({"error": "no such token"}, status=400)
                    resp.del_cookie("sec_token")

                    return resp

                idx, game = idx_game

            args = []

            if find_player:
                args.extend([idx, game])
            if read_data:
                args.append(data)

            resp = await f(self, *args)
            if isinstance(resp, web.Response):
                return resp

            return make_json_response(resp)

        return inner

    return decorator


class GameState:
    def __init__(self, app):
        self.games_in_progress = []
        self.unclaimed_tokens = set()
        self.app = app

        app.router.add_get("/state", self.get_state)
        app.router.add_post("/join_game", self.join_game)
        app.router.add_post("/action/purchase_combinator", self.action_purchase_combinator)
        app.router.add_post("/action/purchase_free_variable", self.action_purchase_free_variable)
        app.router.add_post("/action/bind_variable", self.action_bind_variable)
        app.router.add_post("/action/apply", self.action_apply)
        app.router.add_post("/action/eval", self.action_eval)

        self.game_futures = []

    def add_new_game(self):
        print("Making new game")
        game, p1, p2 = make_standard_game(ExternalPlayer, ExternalPlayer)
        self.games_in_progress.append(game)
        self.unclaimed_tokens.add(p1)
        self.unclaimed_tokens.add(p2)

        asyncio.run_coroutine_threadsafe(game.start_game(), asyncio.get_running_loop())

    def claim_unclaimed_token(self):
        if len(self.unclaimed_tokens) == 0:
            self.add_new_game()

        unclaimed_token = list(self.unclaimed_tokens)[0]
        self.unclaimed_tokens.remove(unclaimed_token)

        return unclaimed_token

    # Gives (i, game) where game.players[i].sec_token == sec_token
    def get_state_for_player(self, sec_token):
        for game in self.games_in_progress:
            for i, pl in enumerate(game.players):
                if pl.sec_token == sec_token:
                    return (i, game)

        return None

    @pl_fn(find_player=True, read_data=False)
    async def get_state(self, i, game):
        return {
            "you_are": i,
            "game": game.to_json_obj()
        }

    async def join_game(self, req):
        tok = self.claim_unclaimed_token()
        resp = web.Response()
        resp.set_cookie("sec_token", tok)

        return resp

    def run(self):
        web.run_app(self.app)

    @pl_fn(find_player=True, read_data=True, expects=["combinator_idx"])
    async def action_purchase_combinator(self, i, game, data):
        await game.players[i].put_action(PurchaseCombinator(data["combinator_idx"]))
        return {}


    @pl_fn(find_player=True, read_data=True, expects=["var_name"])
    async def action_purchase_free_variable(self, i, game, data):
        await game.players[i].put_action(PurchaseFreeVariable(data["var_name"]))
        return {}

    @pl_fn(find_player=True, read_data=True, expects=["bind_name", "deck_idx"])
    async def action_bind_variable(self, i, game, data):
        await game.players[i].put_action(BindVariable(data["bind_name"], data["deck_idx"]))
        return {}

    @pl_fn(find_player=True, read_data=True, expects=["caller_idx", "callee_idx"])
    async def action_apply(self, i, game, data):
        await game.players[i].put_action(Apply(data["caller_idx"], data["callee_idx"]))
        return {}

    @pl_fn(find_player=True, read_data=True, expects=["deck_idx"])
    async def action_eval(self, i, game, data):
        await game.players[i].put_action(Eval(data["deck_idx"]))
        return {}


app = web.Application()

GAME_STATE = GameState(app)
GAME_STATE.run()
