# Discord Ordering Bot

A bot which allows people to buy stuff from you using a discord bot!

## Features

- Portable python script, runs on windows as well as linux
- Simple, beginner friendly deployment
- Integrated crypto payments using Coinbase Commerce
- Integrated Fiat payments using Razorpay
- Uses interactions from discord.py 2.0
- In-built email address verification using SMTP
- Now supports database storage using MongoDB

## Installation

Clone the project into it's seperate folder

```bash
    git clone https://github.com/The-Parth/discord-ordering-bot
```

Grab all the required dependencies simply by running the main file.

```bash
    python main.py
```

As simple as that! Just set up your .ENV variables and you are good to go!
Note: You might have a different python version. In that case, use py, py3 or python3 instead of python.

## Authors and Contributors

- [@The-Parth](https://www.github.com/The-Parth)
- [@manas-b23](https://www.github.com/manas-b23)

## Documentation

- [Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)
- [Coinbase Commerce API reference](https://docs.cloud.coinbase.com/commerce/docs/)

## Environment Variables

To run this project, you will need to add the following environment variables to your `.env` file

#### Discord and Coinbase
1. `TOKEN` = Discord-Bot-Token
2. `CB_TOKEN` = Coinbase-Token
3. `EMAIL_SENDER` = Your own email address
#### SMTP Email Variables
4. `EMAIL_SENDER_NAME` = Name to be displayed on the email
5. `EMAIL_PASSWORD` = Password of the email address (App passwords recommended)
6. `EMAIL_SMTP` = SMTP server of the email address
7. `EMAIL_PORT` = SMTP port of the email address
#### Discord Channel IDs
8. `ORDER_CHANNEL` = Channel ID of the channel where the bot will send the order details
9. `FEEDBACK_CHANNEL` = Channel ID of the channel where the bot will send the feedback
#### Razorpay Variables
10. `RPAY_KEY_ID` = Key ID for Razorpay
11. `RPAY_KEY_SECRET` = Key Secret for Razorpay
#### MongoDB Variables
12. `MONGO_URI` = MongoDB URI

## Usage

Make sure to run the command when Current Working Directory is the same as the one containing the bot.py file

```bash
    python bot.py
```

You can edit the code as per your requirements by reading the code yourself.

####

**Note:** Our Mail is tested to be working with Zoho mail SMTP. Some other mail providers may not work.

To change the otp mails, edit data/carts/otp.html file and change the text as per your requirements.

Razorpay was used in test mode. However, it should work in production mode as well.

MongoDB, if not available, will require you to use the main branch instead of the mongo branch.

This branch is under development and may not be stable.

####
