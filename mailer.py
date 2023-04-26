import smtplib, os, aiosmtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

sender = os.getenv("EMAIL_SENDER")
sender_name = os.getenv("EMAIL_SENDER_NAME")

class Mailer:
    async def async__init__(self):
        try:
            self.server = aiosmtplib.SMTP(hostname='smtp.zoho.in', port=465, use_tls=True)
            print("Connecting to mail server...")
            await self.server.connect()
            print("Connected to mail server")
            await self.server.login(username = sender,password= os.getenv("EMAIL_PASSWORD"), timeout=30)
            print("Logged in to mail server as " + sender)
        except:
            print("Error connecting to mail server")
    
    async def async_send_mail(self, recipient, recipient_name, subject, content):
        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] =  Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender))
        msg['To'] = formataddr((str(Header(recipient_name, 'utf-8')), recipient))
        msg['Cc'] = ""
        msg['Bcc'] = ""
        await self.server.send_message(msg)
        print("Mailed " + recipient)

    def send_mail(self, recipient, subject, content):
        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] =  Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender))
        msg['To'] = recipient
        self.server.sendmail(sender, [recipient], msg.as_string())
        print("Mailed " + recipient)
        
        self.server.sendmail(sender, [recipient], msg.as_string())
    

        