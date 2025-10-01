from services.payment_gateway_adapter import PaymentGatewayAdapter
import requests

class FlutterwaveGateway(PaymentGatewayAdapter):
    """
    Payment gateway adapter for Flutterwave.
    """

    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.base_url = "https://api.flutterwave.com/v3"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def create_charge(self, amount: int, currency: str, source: dict, description: str) -> dict:
        # The 'source' for Flutterwave is a dictionary containing transaction details
        payload = {
            "tx_ref": source['tx_ref'],
            "amount": amount,
            "currency": currency,
            "redirect_url": source['redirect_url'],
            "payment_options": source['payment_options'],
            "customer": {
                "email": source['customer']['email'],
                "name": source['customer']['name']
            },
            "customizations": {
                "title": "Pied Piper Payments",
                "description": description,
                "logo": "https://www.piedpiper.com/app/themes/joystick-v27/images/logo.png"
            }
        }
        try:
            response = requests.post(f"{self.base_url}/payments", json=payload, headers=self._get_headers())
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def create_customer(self, email: str, name: str) -> dict:
        # Flutterwave does not have a separate customer API in the same way as Stripe
        # Customers are created implicitly with transactions.
        return {'email': email, 'name': name}

    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> dict:
        return {'error': 'Not implemented for Flutterwave'}
