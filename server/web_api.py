import asyncio
import sys
from aiohttp import web
from game import make_standard_game
from player import ExternalPlayer
import traceback
import json
from action import *

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("web.log"),
        logging.StreamHandler()
    ]
)


logging.info("started")

def verify_username(name):
    if len(name) > 40:
        return False
    if '\x1b' in name: # No escape codes!
        return False

    return True

def make_json_response(data, status=200):
    return web.Response(
        body=json.dumps(data),
        content_type='application/json',
        status=status,
    )

def pl_fn(*, find_game, find_player, expects=None, do_log=True):
    if find_player and not find_game:
        raise ValueError("find_player = True, but find_game = False!")
    def decorator(f):
        nonlocal do_log
        async def inner(self, req):
            nonlocal do_log
            try:
                rdata = await req.text()
                if rdata == '':
                    data = {}
                else:
                    data = json.loads(rdata)
                    if expects is not None:
                        for key in expects:
                            if key not in data:
                                return make_json_response({"expected": expects, "missing": key}, status=400)
            except json.JSONDecodeError as e:
                logging.warning(f"JSON decode error in {f.__name__}: {e}")
                return make_json_response({"error": "invalid json!"}, status=400)

            if find_game:
                if "game_id" in req.query:
                    game_id = req.query["game_id"]
                else:
                    # TODO: maybe give a default id? reroute to /lobby?
                    return make_json_response({"error": "missing game_id"}, status=400)

                game = self.get_game(game_id)
                if game is None:
                    return make_json_response({"error": "no such game!"}, status=400)

            if find_player:
                if not 'sec_token' in data:
                    if find_player == 'noerror':
                        idx = None
                    else:
                        return make_json_response({"error": "missing sec_token"}, status=400)
                else:
                    idx = game.player_with_token(data["sec_token"])

                    if idx is None and find_player != "noerror":
                        resp = make_json_response({"error": "no such token"}, status=400)

                        return resp

            args = [data]

            if find_player:
                args.append(idx)
            if find_game:
                args.append(game)

            if do_log:
                log = f"{req.remote} accessing {req.rel_url}. "
                if find_game:
                    log += f"Game = {game.game_identifier}"
                if find_player and idx != None:
                    log += f" as {game.players[idx].user_name}/{game.players[idx].sec_token}"
                logging.info(log)

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

        app.router.add_get("/", self.index)

        app.router.add_post("/api/state", self.get_state)
        app.router.add_post("/api/get_games", self.get_games)
        app.router.add_post("/api/create_new_game", self.create_new_game)
        app.router.add_post("/api/join_game", self.join_game)
        app.router.add_post("/api/action/purchase_combinator", self.action_purchase_combinator)
        app.router.add_post("/api/action/purchase_free_variable", self.action_purchase_free_variable)
        app.router.add_post("/api/action/bind_variable", self.action_bind_variable)
        app.router.add_post("/api/action/apply", self.action_apply)
        app.router.add_post("/api/action/eval", self.action_eval)

        app.router.add_static("/", '../static')

        self.game_futures = []

    async def index(self, req):
        return web.Response(
            body=open("../static/lobby.html", "r").read(),
            content_type='text/html',
            status=200,
        )

    def claim_unclaimed_token(self):
        if len(self.unclaimed_tokens) == 0:
            self.add_new_game()

        unclaimed_token = list(self.unclaimed_tokens)[0]
        self.unclaimed_tokens.remove(unclaimed_token)

        logging.info(f"User claiming token {unclaimed_token}")
        return unclaimed_token

    # Gives game or None
    def get_game(self, game_id):
        for game in self.games_in_progress:
            if game.game_identifier == game_id:
                return game

        return None

    @pl_fn(find_game=False, find_player=False, do_log=False)
    async def get_games(self, _data):
        return {
            "games": [game.to_json_obj() for game in self.games_in_progress]
        }

    @pl_fn(find_game=False, find_player=False)
    async def create_new_game(self, _data):
        game, _p1, _p2 = make_standard_game(ExternalPlayer, ExternalPlayer)
        self.games_in_progress.append(game)

        asyncio.run_coroutine_threadsafe(game.start_game(), asyncio.get_running_loop())

        logging.info(f"Created new game with name {game.game_identifier}")
        return {"created_id": game.game_identifier}

    @pl_fn(find_game=True, find_player=False, expects=["player_idx", "name"])
    async def join_game(self, data, game):
        try:
            pl = game.players[data["player_idx"]]
        except:
            return make_json_response({"error": "invalid player_idx"}, status=400)

        if type(data["name"]) == str:
            if not verify_username(data["name"]):
                return make_json_response({"error": "name does not meet rules"}, status=400)

            sec_token = await pl.claim(data["name"])
            if sec_token == None:
                return make_json_response({"error": "player already claimed"}, status=400)
            else:
                logging.info(f"User sec_token={sec_token} claimed as {pl.user_name}")
                return make_json_response({"new_sec_token": sec_token})
        else:
            return make_json_response({"error": "invalid name"}, status=400)

    @pl_fn(find_game=True, find_player='noerror', do_log=False)
    async def get_state(self, _data, i, game):
        return {
            "game": game.to_json_obj(),
            "you_are": i,
        }

    def run(self, port):
        web.run_app(self.app, access_log=False, port=port)

    @pl_fn(find_game=True, find_player=True, expects=["combinator_idx"])
    async def action_purchase_combinator(self, data, i, game):
        await game.players[i].put_action(PurchaseCombinator(data["combinator_idx"]))
        return {}


    @pl_fn(find_game=True, find_player=True, expects=["var_name"])
    async def action_purchase_free_variable(self, data, i, game):
        await game.players[i].put_action(PurchaseFreeVariable(data["var_name"]))
        return {}

    @pl_fn(find_game=True, find_player=True, expects=["bind_name", "deck_idx"])
    async def action_bind_variable(self, data, i, game):
        await game.players[i].put_action(BindVariable(data["bind_name"], data["deck_idx"]))
        return {}

    @pl_fn(find_game=True, find_player=True, expects=["caller_idx", "callee_idx"])
    async def action_apply(self, data, i, game):
        await game.players[i].put_action(Apply(data["caller_idx"], data["callee_idx"]))
        return {}

    @pl_fn(find_game=True, find_player=True, expects=["deck_idx"])
    async def action_eval(self, data, i, game):
        await game.players[i].put_action(Eval(data["deck_idx"]))
        return {}


app = web.Application()

GAME_STATE = GameState(app)

logging.getLogger('asyncio').setLevel(logging.WARNING)

if len(sys.argv) == 2:
    GAME_STATE.run(port=int(sys.argv[1]))
else:
    GAME_STATE.run(port=8080)
