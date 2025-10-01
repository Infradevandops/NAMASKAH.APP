from abc import ABC, abstractmethod

class PaymentGatewayAdapter(ABC):
    """
    Abstract base class for a payment gateway adapter.
    This class defines the interface for interacting with different payment gateways.
    """

    @abstractmethod
    def create_charge(self, amount: int, currency: str, source: str, description: str) -> dict:
        """
        Create a charge or payment.

        Args:
            amount: The amount to charge, in the smallest currency unit (e.g., cents).
            currency: The three-letter ISO currency code.
            source: The payment source (e.g., a card token).
            description: A description for the charge.

        Returns:
            A dictionary containing the charge details.
        """
        pass

    @abstractmethod
    def create_customer(self, email: str, name: str) -> dict:
        """
        Create a customer.

        Args:
            email: The customer's email address.
            name: The customer's name.

        Returns:
            A dictionary containing the customer details.
        """
        pass

    @abstractmethod
    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> dict:
        """
        Attach a payment method to a customer.

        Args:
            customer_id: The ID of the customer.
            payment_method_id: The ID of the payment method.

        Returns:
            A dictionary containing the payment method details.
        """
        pass
