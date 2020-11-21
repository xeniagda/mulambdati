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

def pl_fn(*, find_game, find_player, read_data, expects=None, do_log=True):
    if not read_data and expects is not None:
        raise ValueError("read_data = False, expects != None")
    if find_player and not find_game:
        raise ValueError("find_player = True, but find_game = False!")
    def decorator(f):
        nonlocal do_log
        async def inner(self, req):
            nonlocal do_log
            if read_data:
                try:
                    data = await req.json()
                    for key in expects:
                        if key not in data:
                            return make_json_response({"expected": expects, "missing": key}, status=400)
                except Exception as e:
                    logging.warning(f"JSON decode error: {e}")
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
                if not 'sec_token' in req.cookies:
                    if find_player == 'noerror':
                        idx = None
                    else:
                        return make_json_response({"error": "missing sec_token"}, status=400)
                else:
                    idx = game.player_with_token(req.cookies["sec_token"])

                    if idx is None and find_player != "noerror":
                        resp = make_json_response({"error": "no such token"}, status=400)
                        resp.del_cookie("sec_token")

                        return resp

            args = []

            if find_player:
                args.append(idx)
            if find_game:
                args.append(game)
            if read_data:
                args.append(data)

            if do_log:
                log = f"{req.remote} accessing {req.rel_url}. "
                if find_game:
                    log += f"Game = {game.game_identifier}"
                if find_player and idx != None:
                    log += f" as {game.players[idx].name}/{game.players[idx].sec_token}"
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

        app.router.add_get("/api/state", self.get_state)
        app.router.add_get("/api/get_games", self.get_games)
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

    @pl_fn(find_game=False, find_player=False, read_data=False, do_log=False)
    async def get_games(self):
        return {
            "games": [game.to_json_obj() for game in self.games_in_progress]
        }

    @pl_fn(find_game=False, find_player=False, read_data=False)
    async def create_new_game(self):
        game, _p1, _p2 = make_standard_game(ExternalPlayer, ExternalPlayer)
        self.games_in_progress.append(game)

        asyncio.run_coroutine_threadsafe(game.start_game(), asyncio.get_running_loop())

        logging.info(f"Created new game with name {game.game_identifier}")
        return {"created_id": game.game_identifier}

    @pl_fn(find_game=True, find_player=False, read_data=True, expects=["player_idx", "name"])
    async def join_game(self, game, data):
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
                resp = web.Response()
                resp.set_cookie("sec_token", sec_token)

                return resp
        else:
            return make_json_response({"error": "invalid name"}, status=400)

    @pl_fn(find_game=True, find_player='noerror', read_data=False, do_log=False)
    async def get_state(self, i, game):
        return {
            "game": game.to_json_obj(),
            "you_are": i,
        }

    def run(self, port):
        web.run_app(self.app, access_log=False, port=port)

    @pl_fn(find_game=True, find_player=True, read_data=True, expects=["combinator_idx"])
    async def action_purchase_combinator(self, i, game, data):
        await game.players[i].put_action(PurchaseCombinator(data["combinator_idx"]))
        return {}


    @pl_fn(find_game=True, find_player=True, read_data=True, expects=["var_name"])
    async def action_purchase_free_variable(self, i, game, data):
        await game.players[i].put_action(PurchaseFreeVariable(data["var_name"]))
        return {}

    @pl_fn(find_game=True, find_player=True, read_data=True, expects=["bind_name", "deck_idx"])
    async def action_bind_variable(self, i, game, data):
        await game.players[i].put_action(BindVariable(data["bind_name"], data["deck_idx"]))
        return {}

    @pl_fn(find_game=True, find_player=True, read_data=True, expects=["caller_idx", "callee_idx"])
    async def action_apply(self, i, game, data):
        await game.players[i].put_action(Apply(data["caller_idx"], data["callee_idx"]))
        return {}

    @pl_fn(find_game=True, find_player=True, read_data=True, expects=["deck_idx"])
    async def action_eval(self, i, game, data):
        await game.players[i].put_action(Eval(data["deck_idx"]))
        return {}


app = web.Application()

GAME_STATE = GameState(app)

logging.getLogger('asyncio').setLevel(logging.WARNING)

if len(sys.argv) == 2:
    GAME_STATE.run(port=int(sys.argv[1]))
else:
    GAME_STATE.run(port=8080)
