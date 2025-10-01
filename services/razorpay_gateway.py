from services.payment_gateway_adapter import PaymentGatewayAdapter
import razorpay

class RazorpayGateway(PaymentGatewayAdapter):
    """
    Payment gateway adapter for Razorpay.
    """

    def __init__(self, key_id, key_secret):
        self.client = razorpay.Client(auth=(key_id, key_secret))

    def create_charge(self, amount: int, currency: str, source: str, description: str) -> dict:
        try:
            # Razorpay uses 'notes' for description
            payment = self.client.payment.capture(source, amount, {"currency": currency, "notes": {"description": description}})
            return payment
        except Exception as e:
            return {'error': str(e)}

    def create_customer(self, email: str, name: str) -> dict:
        try:
            customer = self.client.customer.create({
                'name': name,
                'email': email
            })
            return customer
        except Exception as e:
            return {'error': str(e)}

    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> dict:
        # Razorpay does not have a direct equivalent to attaching a payment method
        # in the same way as Stripe. This would typically be handled on the client-side.
        return {'error': 'Not implemented for Razorpay'}
