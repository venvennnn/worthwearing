import os

# Unit tests must not call the live Perfect Corp API or consume units.
os.environ["DEMO_MODE"] = "true"
os.environ["PERFECT_CORP_API_KEY"] = ""

from app.store import load_demo


def closet():
    return load_demo().closet


def candidates():
    return {item.id: item for item in load_demo().candidates}


def shopper():
    return load_demo().shopper
