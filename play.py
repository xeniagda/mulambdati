import sys
import asyncio
from aiofiles import open as async_open

from player import ConsolePlayer
from game import Game, make_standard_game

import json

async def start():
    tty1i, tty1o, tty2i, tty2o = sys.argv[1:5]


    it1 = await async_open(tty1i, "r")
    ot1 = await async_open(tty1o, "w")
    it2 = await async_open(tty2i, "r")
    ot2 = await async_open(tty2o, "w")
    await ot1.write("=== RESTART ===\n"); await ot1.flush()
    await ot2.write("=== RESTART ===\n"); await ot2.flush()

    pl1_const = lambda id, health, mana: ConsolePlayer(id, 10, 0, it1, ot1)
    pl2_const = lambda id, health, mana: ConsolePlayer(id, 10, 0, it2, ot2)

    game, _, _ = make_standard_game(pl1_const, pl2_const)

    print(json.dumps(game.to_json_obj()))

    await game.start_game()

asyncio.run(start())
