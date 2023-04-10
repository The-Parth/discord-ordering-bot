import requests

API_ENDPOINT = 'https://discord.com/api/v10'
CLIENT_ID = '1087399132290883677'
CLIENT_SECRET = 'nW8YSQ4_6y4gEhZIyIVm9vKn6WJE2mA3'
REDIRECT_URI = 'https://parthb.xyz/auth'


def exchange_code(code):
    data = {
        "Authorization": "Bearer " + code,
    }
    return requests.get("%s/users/@me" % API_ENDPOINT, headers=data)

print(exchange_code("7JUeHicqrzdqm7ghz6gxNWDnuNtrxC"))
