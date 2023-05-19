import requests
import os
import datetime
from dotenv import load_dotenv
from extras import PaymentClass

load_dotenv()

KEY_ID = os.getenv('RPAY_KEY_ID')
KEY_SECRET = os.getenv('RPAY_KEY_SECRET')
RPAY_URL = "https://api.razorpay.com/v1/"

# Here we use Razorpay's Payment Links API to create a payment link


class Razorpay(PaymentClass):
    """
    This class handles the payment process using Razorpay's Payment Links API.
    """
    def invoice(name: str, email: str, price: float, denomination: str, desc: str) -> dict:
        # URL for Razorpay API to create a payment link
        url = RPAY_URL + 'payment_links'
        if price <= 0:
            raise ValueError("Amount must be greater than 0")
        # Headers required by Razorpay API
        headers = {
            'Content-type': 'application/json',
        }
        # Body for the POST request to API
        body = {
            "amount": int(price*100),
            "currency": denomination,
            "description": desc,
            "customer": {
                "name": name,
                "email": email
            },
            "notify": {
                "sms": False,
                "email": True
            },
            "reminder_enable": True,
            "notes": {
                "description": desc
            },
            "expire_by": int(datetime.datetime.now().timestamp()) + 3600
        }

        # POST request to Razorpay API, with try/except block to catch errors
        try:
            # Making the request
            response = requests.post(
                url, headers=headers, json=body, auth=(KEY_ID, KEY_SECRET))
            json_response = response.json()
            id = json_response["id"]
            invoice_url = json_response["short_url"]
            code = id
            print(invoice_url, id)
            return {"url": invoice_url, "id": id, "code": code}
        except Exception as e:
            print(e)

    # Method to check if a payment has been paid or is pending, using Razorpay API
    def check(id: str) -> str:
        if KEY_ID == None or KEY_SECRET == None:
            return "ERROR: Razorpay API keys not found"
        # Payment URL and ID
        url = RPAY_URL + 'payment_links/' + id

        # Headers required by Razorpay API
        headers = {
            'Content-type': 'application/json'
        }

        # Get request to Razorpay API
        response = requests.get(url, headers=headers,
                                auth=(KEY_ID, KEY_SECRET))
        status: str
        status = response.json()["status"]
        status = status.upper()
        return status

    # Method to void a payment, using Razorpay API
    def void_payment(id: str, id_pass = False):
        if KEY_ID == None or KEY_SECRET == None:
            return "ERROR: Razorpay API keys not found"

        # Payment VOID Endpoint
        url = RPAY_URL + 'payment_links/' + id + '/cancel'

        # Headers required by Razorpay API
        headers = {
            'Content-type': 'application/json'
        }

        # POST request to Razorpay API
        response = requests.post(url, headers=headers,
                                 auth=(KEY_ID, KEY_SECRET))
        status = Razorpay.check_payments(id, True)
        if status == "CANCELLED":
            return "Payment cancelled successfully"
        elif status == "EXPIRED":
            return "Payment already expired"
        elif status == "PAID" or status == "PARTIALLY_PAID":
            return "Payment already paid"
        else:
            return "Payment could not be cancelled"
        
    def get_link(inv_id) -> str:
        if KEY_ID == None or KEY_SECRET == None:
            return "http://txti.es/ijro8"
        
        url = RPAY_URL + 'payment_links/' + inv_id
        headers = {
            'Content-type': 'application/json'
        }
        response = requests.get(url, headers=headers, auth=(KEY_ID, KEY_SECRET))
        return response.json()['short_url']

    def check_payments(inv, id_pass = False):
        """Check if a payment has been paid or is pending, using Razorpay API"""
        if not id_pass:
            inv = inv['id']
        status = Razorpay.check(inv)
        return status.upper()
    
    


    
        

