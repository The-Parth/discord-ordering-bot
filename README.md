
# Discord Ordering Bot

A bot which allows people to buy stuff from you using a discord bot!



## Features
- Portable python script, runs on windows as well as linux
- Easy deployment
- Integrated crypto payments
- Uses interactions from discord.py 2.0

## Installation

Clone the project into it's seperate folder

```bash
    git clone https://github.com/The-Parth/discord-ordering-bot
```
Grab all the required dependencies.
```bash
    pip install discord
    pip install python-dotenv
    pip install requests
```
Go and delete all files in `data/carts` and fill `data/newmenu.json` with your menu files!

## Authors and Contributors

- [@The-Parth](https://www.github.com/The-Parth)
- [@manas-b23](https://www.github.com/manas-b23)




## Documentation

- [Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)
- [Coinbase Commerce API reference](https://docs.cloud.coinbase.com/commerce/docs/)


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

1. `TOKEN` = Discord-Bot-Token
2. `CB_TOKEN` = Coinbase-Token


## Usage
Make sure to run the command when Current Working Directory is the same as the one containing the bot.py file
```bash
    python bot.py
```
You can edit the code as per your requirements by reading the code yourself. 

