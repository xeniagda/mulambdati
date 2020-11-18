import random

def make_random_token():
    return "apio" + str(random.randrange(0, 2<<32))
