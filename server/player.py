from abc import ABC, abstractmethod
from action import *
import asyncio
from token_gen import make_random_token

class Player(ABC):
    def __init__(self, sec_token, health, mana):
        self.sec_token = sec_token # Given to a client on game start, kept secret and used to """authenticate"""
        self.health = health
        self.mana = mana
        self.deck = []

    @abstractmethod
    async def update_state(self, game):
        pass

    @abstractmethod
    async def get_action(self):
        pass

    @abstractmethod
    async def tell_msg(self, msg):
        pass

    def to_json_obj(self):
        return {
            "health": self.health,
            "mana": self.mana,
            "deck": [
                {
                    "structure": term.to_json_obj(),
                    "rendered": str(term),
                    "free-vars": list(term.free_variables()),
                    "id": term.id,
                }
                for term in self.deck
            ],
        }

class ExternalPlayer(Player):
    def __init__(self, sec_token, health, mana):
        super(ExternalPlayer, self).__init__(sec_token, health, mana)

        self.current_state = None
        self.action_queue = asyncio.Queue()
        self.msg_list = [] # (random id, msg), id filtered by the client

    async def update_state(self, game):
        self.current_state = game

    async def get_action(self):
        return await self.action_queue.get()

    async def tell_msg(self, msg):
        self.msg_list.append((make_random_token(), msg))

    async def put_action(self, action):
        await self.action_queue.put(action)

    def to_json_obj(self):
        orig = super().to_json_obj()
        orig["msg_list"] = [{"id": rid, "msg": msg} for rid, msg in self.msg_list]
        return orig

class ConsolePlayer(Player):
    def __init__(self, sec_token, health, mana, f_in, f_out):
        super(ConsolePlayer, self).__init__(sec_token, health, mana)

        self.f_out = f_out
        self.f_in = f_in

        self.purchasable_combinators = []
        self.surpress_state = False

    async def update_state(self, game):
        if self.surpress_state:
            return

        self.purchasable_combinators = game.combinators
        for pl, name in [(game.players[0], "Player one"), (game.players[1], "Player two")]:
            tag = ""
            if pl is self:
                tag = " (you!)"
            await self.f_out.write(f"{name}{tag}:\n")
            await self.f_out.write(f"    Health/Mana: {pl.health}/{pl.mana}\n")
            await self.f_out.write("    Deck:\n")
            for i, card in enumerate(pl.deck):
                await self.f_out.write(f"        {i}: {card}\n")

        await self.f_out.flush()

    async def tell_msg(self, action):
        await self.f_out.write(f"[!! {action} !!]\n")
        await self.f_out.flush()

    async def get_action(self):
        await self.f_out.write("Press enter to start action!\n")
        await self.f_in.readline()

        self.surpress_state = True
        await self.f_out.write("What to do (buy [c]ombinator, buy free [v]ariable, [b]ind variable, [a]pply, [e]val) ")
        await self.f_out.flush()

        choice = (await self.f_in.readline()).strip()
        if choice == 'c':
            await self.f_out.write("Combinators:\n")
            for i, comb in enumerate(self.purchasable_combinators):
                await self.f_out.write(f"    {i}: {comb.name}: costs {comb.price}𐌼\n")

            await self.f_out.write("Purchase combinator (idx)? ")
            await self.f_out.flush()
            return PurchaseCombinator(int((await self.f_in.readline()).strip()))

        if choice == 'v':
            await self.f_out.write("Variable name? ")
            await self.f_out.flush()
            return PurchaseFreeVariable((await self.f_in.readline()).strip())

        if choice == 'b':
            await self.f_out.write("What deck position to bind? ")
            await self.f_out.flush()
            row = int((await self.f_in.readline()).strip())
            await self.f_out.write("Variable name (idx)? ")
            await self.f_out.flush()
            name = (await self.f_in.readline()).strip()

            return BindVariable(row, name)

        if choice == 'a':
            await self.f_out.write("What deck position to call? ")
            await self.f_out.flush()
            call = int((await self.f_in.readline()).strip())
            await self.f_out.write("What deck position as argument? ")
            await self.f_out.flush()
            arg = int((await self.f_in.readline()).strip())

            return Apply(call, arg)

        if choice == 'e':
            await self.f_out.write("What deck position to eval? ")
            await self.f_out.flush()
            return Eval(int((await self.f_in.readline()).strip()))

        return await self.get_action()
