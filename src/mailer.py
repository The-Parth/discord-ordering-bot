import os, aiosmtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

sender = os.getenv("EMAIL_SENDER")
sender_name = os.getenv("EMAIL_SENDER_NAME")
smtp = os.getenv("EMAIL_SMTP")
port = os.getenv("EMAIL_PORT")


""" 
We have used the aiosmtplib library to send emails asynchronously.
Simple SMTP can hog the main thread and cause the bot to lag.
Asynchronous SMTP is a better option in my opinion for our use case as we have limited resources.
Our bot is not one dedicated to sending emails only, so we can use the resources for other tasks.
"""

class Mailer:
    async def async__init__(self):
        """Initializes the SMTP server object and logs in to it"""
        try:
            # Provide the SMTP server details here
            self.server = aiosmtplib.SMTP(hostname=smtp, port=port, use_tls=True)
            print("Connecting to mail server...")
            # Connect to the server
            await self.server.connect()
            print("Connected to mail server")
            
            # Login to the server
            await self.server.login(username = sender,password= os.getenv("EMAIL_PASSWORD"))
            print("Logged in to mail server as " + sender)
        except:
            print("Error connecting to mail server")
    
    async def async_send_mail(self, recipient, recipient_name, subject, content):
        """Sends an email to the recipient, with the given subject and content
        recipient: The email address of the recipient
        recipient_name: The name of the recipient
        subject: The subject of the email
        content: The content of the email
        
        This function sends the email asynchronously without blocking the main thread.
        """
        
        # Create the message
        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] =  Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender))
        msg['To'] = formataddr((str(Header(recipient_name, 'utf-8')), recipient))
        msg['Cc'] = ""
        msg['Bcc'] = ""
        while True:
            try:
                # Send the message
                await self.server.send_message(msg)
                print("Mailed " + recipient)
                return
            except aiosmtplib.SMTPServerDisconnected:
                # If the server disconnects, reconnect and try again
                print("Server disconnected, reconnecting...")
                try:
                    self.server = aiosmtplib.SMTP(hostname=smtp, port=port, use_tls=True)
                    await self.server.connect()
                    await self.server.login(username = sender,password= os.getenv("EMAIL_PASSWORD"))
                    print("Logged in to mail server as " + sender)
                except:
                    # If the server cannot be connected to, return
                    print("Error connecting to mail server")
            except:
                # If the email cannot be sent for any other reason, return
                print("Error sending mail to " + recipient)
                return

    

        