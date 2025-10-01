from services.payment_gateway_adapter import PaymentGatewayAdapter
import requests

class PaystackGateway(PaymentGatewayAdapter):
    """
    Payment gateway adapter for Paystack.
    """

    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.base_url = "https://api.paystack.co"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def create_charge(self, amount: int, currency: str, source: dict, description: str) -> dict:
        # The 'source' for Paystack is a dictionary containing transaction details
        payload = {
            "email": source['email'],
            "amount": amount * 100,  # Paystack expects amount in kobo
            "currency": currency,
            "metadata": {
                "description": description
            }
        }
        try:
            response = requests.post(f"{self.base_url}/transaction/initialize", json=payload, headers=self._get_headers())
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def create_customer(self, email: str, name: str) -> dict:
        # Paystack creates customers implicitly with transactions or can be created separately
        payload = {
            "email": email,
            "first_name": name.split(' ')[0],
            "last_name": ' '.join(name.split(' ')[1:])
        }
        try:
            response = requests.post(f"{self.base_url}/customer", json=payload, headers=self._get_headers())
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> dict:
        return {'error': 'Not implemented for Paystack'}
