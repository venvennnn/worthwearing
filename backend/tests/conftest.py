from app.store import load_demo


def closet():
    return load_demo().closet


def candidates():
    return {item.id: item for item in load_demo().candidates}


def shopper():
    return load_demo().shopper
