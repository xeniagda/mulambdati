from expr import Application, Variable, Abstraction
from monad_io import EvalIO
from abc import ABC, abstractmethod

class Action:
    def __init__(self, combinators, fvs, abstractions, deck_combine, eval_terms):
        self.combinators = combinators
        self.fvs = fvs # [str]
        self.abstractions = abstractions # [(int, str)]
        self.deck_combine = deck_combine
        self.eval_terms = eval_terms

    def __str__(self):
        return\
            f"Action(combinators={self.combinators}, " +\
            "fvs={self.fvs}, abstractions={self.abstractions}, " +\
            "deck_combine={self.deck_combine}, eval_terms={self.eval_terms})"

    def run(self, game):
        player = game.players[game.turn]

        player.mana += 1
        for p in self.combinators:
            price, _name, term = game.combinators[p]
            player.mana -= price
            player.deck.append(term)

        for fv in self.fvs:
            player.deck.append(Variable(fv))
            player.mana -= 2

        for row, name in self.abstractions:
            player.deck[row] = Abstraction(name, player.deck[row])
            player.mana -= 2

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
            self.f_out.write("    Deck:\n")
            for i, card in enumerate(pl.deck):
                self.f_out.write(f"        {i}: {card}\n")

        self.f_out.flush()

    async def tell_action(self, action):
        self.f_out.write(f"[!! {action} !!]\n")
        self.f_out.flush()

    async def get_action(self):
        self.f_out.write("Your turn!\n")
        self.f_out.write("Combinators:\n")
        for i, (price, name, term) in enumerate(self.purchasable_combinators):
            self.f_out.write(f"    {i}: {name}: costs {price}𐌼\n")

        self.f_out.write("Purchase combinators? (comb),* ")
        self.f_out.flush()

        combinators = [int(x) for x in self.f_in.readline().strip().split(",") if x]

        self.f_out.write("Purchase free variables (2𐌼 per variable) (name),*? ")
        self.f_out.flush()

        fvs = [x for x in self.f_in.readline().strip().split(",") if x]

        self.f_out.write("Abstractions (2𐌼)  (enter (row-name2caputre)-*),* ")
        self.f_out.flush()

        abstractions = [(int(x.split("-")[0]), x.split("-")[1]) for x in self.f_in.readline().strip().split(",") if x]

        self.f_out.write("Combines (f-x),* ")
        self.f_out.flush()
        combines = [(int(y) for y in x.split("-")) for x in self.f_in.readline().strip().split(",") if x]

        self.f_out.write("Evals (f),* ")
        self.f_out.flush()
        evals = [int(x) for x in self.f_in.readline().strip().split(",") if x]

        return Action(combinators, fvs, abstractions, combines, evals)
