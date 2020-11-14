from expr import Application
from monad_io import EvalIO
from abc import ABC, abstractmethod

class Action:
    def __init__(self, combinator_purchases, deck_combine, eval_terms):
        self.combinator_purchases = combinator_purchases
        self.deck_combine = deck_combine
        self.eval_terms = eval_terms

    def __str__(self):
        return f"Action(combinator_purchases={self.combinator_purchases}, deck_combine={self.deck_combine}, eval_terms={self.eval_terms})"

    def run(self, game):
        player = game.players[game.turn]

        player.mana += 1
        for p in self.combinator_purchases:
            price, _name, term = game.combinators[p]
            player.mana -= price
            player.deck.append(term)

        for (s1, s2) in self.deck_combine:
            player.deck[s1] = Application(player.deck[s1], player.deck[s2]).whnf()
            del player.deck[s2]

        for e in self.eval_terms:
            term = EvalIO(game.layout, player.deck[e])
            player.deck[e] = term.whnf()

class Player(ABC):
    def __init__(self, health, mana):
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
    async def tell_action(self, action):
        pass

class ConsolePlayer(Player):
    def __init__(self, health, mana, f_in, f_out):
        super(ConsolePlayer, self).__init__(health, mana)

        self.f_out = f_out
        self.f_in = f_in

        self.purchasable_combinators = []

    async def update_state(self, game):
        self.purchasable_combinators = game.combinators
        for pl, name in [(game.players[0], "Player one"), (game.players[1], "Player two")]:
            tag = ""
            if pl is self:
                tag = " (you!)"
            self.f_out.write(f"{name}{tag}:\n")
            self.f_out.write(f"    Health/Mana: {pl.health}/{pl.mana}\n")
            self.f_out.write(f"    Deck: {pl.deck}\n")

        self.f_out.flush()

    async def tell_action(self, action):
        self.f_out.write(f"[!! {action} !!]\n")
        self.f_out.flush()

    async def get_action(self):
        self.f_out.write("Your turn!\n")
        self.f_out.write("Combinators:\n")
        for i, (price, name, term) in enumerate(self.purchasable_combinators):
            self.f_out.write(f"    {i}: {name}: costs {price}𐌼\n")

        self.f_out.write("Purchases? ")
        self.f_out.flush()

        purchases = [int(x) for x in self.f_in.readline().strip().split(" ") if x]

        self.f_out.write("Combines ( /,)? ")
        self.f_out.flush()
        combines = [(int(y) for y in x.split()) for x in self.f_in.readline().strip().split(",") if x]

        self.f_out.write("Evals ( )? ")
        self.f_out.flush()
        evals = [int(x) for x in self.f_in.readline().strip().split(" ") if x]

        return Action(purchases, combines, evals)
