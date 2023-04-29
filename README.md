
# Discord Ordering Bot

A bot which allows people to buy stuff from you using a discord bot!



## Features
- Portable python script, runs on windows as well as linux
- Easy deployment
- Integrated crypto payments
- Uses interactions from discord.py 2.0
- In-built email address verification using SMTP

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
    pip install aiosmtplib
```
As simple as that! Just set up your .ENV variables and you are good to go!

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
3. `EMAIL_SENDER` = Your own email address
4. `EMAIL_SENDER_NAME` = Name to be displayed on the email
5. `EMAIL_PASSWORD` = Password of the email address (App passwords recommended)
6. `EMAIL_SMTP` = SMTP server of the email address
7. `EMAIL_PORT` = SMTP port of the email address
8. `ORDER_CHANNEL` = Channel ID of the channel where the bot will send the order details
9. `FEEDBACK_CHANNEL` = Channel ID of the channel where the bot will send the feedback




## Usage
Make sure to run the command when Current Working Directory is the same as the one containing the bot.py file
```bash
    python bot.py
```
You can edit the code as per your requirements by reading the code yourself. 
####
**Note:** Our Mail is tested to be working with Zoho mail SMTP. Some other mail providers may not work.

To change the otp mails, edit data/carts/otp.html file and change the text as per your requirements. 
####

