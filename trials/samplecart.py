cart = {
    0: {
        "name": {
            "quantity": 1,
            "rate": 100,
            "total": 100*1
        }
    },
    1: {
        "item1": {
            "quantity": 3,
            "rate": 120,
            "total": 120*3
        },
        "item2": {
            "quantity": 2,
            "rate": 150,
            "total": 150*2
        }
    }
}

import json
f = json.dumps(cart[1],indent=2)
with open("data/carts/1.json","w") as file:
    file.write(f)