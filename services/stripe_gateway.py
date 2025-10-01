from services.payment_gateway_adapter import PaymentGatewayAdapter
import stripe

class StripeGateway(PaymentGatewayAdapter):
    """
    Payment gateway adapter for Stripe.
    """

    def __init__(self, api_key):
        stripe.api_key = api_key

    def create_charge(self, amount: int, currency: str, source: str, description: str) -> dict:
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=source,
                description=description
            )
            return charge
        except stripe.error.StripeError as e:
            # Handle Stripe-specific errors
            return {'error': str(e)}

    def create_customer(self, email: str, name: str) -> dict:
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            return customer
        except stripe.error.StripeError as e:
            return {'error': str(e)}

    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> dict:
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            return payment_method
        except stripe.error.StripeError as e:
            return {'error': str(e)}
