def dictmaker(n:int) -> dict:
    digs = digits(n)
    d = {}
    for i in digs:
        if i in d:
            d[i] += 1
        else:
            d[i] = 1
    return d

def digits(n:int) -> list:
    digs = []
    while n > 0:
        digs.append(n % 10)
        n //= 10
    return digs

for i in range(0,10000):
    if dictmaker(i) == dictmaker(701):
        print(i)