import random

words = open("/usr/share/dict/words", "r").read().split("\n")
def make_random_token():
    return "apio" + random.choice(words) + random.choice(words)
