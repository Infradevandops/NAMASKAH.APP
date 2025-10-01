from datetime import datetime
from services.payment_gateway_adapter import PaymentGatewayAdapter

class BillingService:
    """
    Service for handling billing logic, including prorated calculations and payments.
    """

    def __init__(self, payment_gateway: PaymentGatewayAdapter):
        self.payment_gateway = payment_gateway

    def calculate_prorated_amount(self, old_plan_cost: int, new_plan_cost: int, remaining_days: int, total_days_in_cycle: int) -> int:
        """
        Calculate the prorated amount for a plan change.

        Args:
            old_plan_cost: The cost of the old plan.
            new_plan_cost: The cost of the new plan.
            remaining_days: The number of remaining days in the billing cycle.
            total_days_in_cycle: The total number of days in the billing cycle.

        Returns:
            The prorated amount to be charged or credited.
        """
        daily_rate_old = old_plan_cost / total_days_in_cycle
        daily_rate_new = new_plan_cost / total_days_in_cycle

        credit_for_old_plan = daily_rate_old * remaining_days
        cost_for_new_plan = daily_rate_new * remaining_days

        return round(cost_for_new_plan - credit_for_old_plan)

    def change_subscription(self, user_id: str, new_plan: dict, old_plan: dict) -> dict:
        """
        Change a user's subscription and handle the prorated billing.

        Args:
            user_id: The ID of the user.
            new_plan: A dictionary representing the new plan.
            old_plan: A dictionary representing the old plan.

        Returns:
            A dictionary containing the result of the subscription change.
        """
        # Assuming a 30-day billing cycle for simplicity
        total_days_in_cycle = 30
        # This would be calculated based on the subscription start date
        remaining_days = 15 

        prorated_amount = self.calculate_prorated_amount(
            old_plan['cost'],
            new_plan['cost'],
            remaining_days,
            total_days_in_cycle
        )

        if prorated_amount > 0:
            # Charge the user
            charge = self.payment_gateway.create_charge(
                amount=prorated_amount,
                currency='usd',
                source='tok_visa',  # This would be a real token
                description=f'Prorated charge for plan change to {new_plan["name"]}'
            )
            return {'status': 'success', 'charge': charge}
        else:
            # Credit the user's account (implementation would vary)
            return {'status': 'success', 'credit': -prorated_amount}
