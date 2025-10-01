from fastapi import APIRouter, Depends, Query
from services.billing_service import BillingService
from services.payment_gateway_adapter import PaymentGatewayAdapter
from services.stripe_gateway import StripeGateway
from services.razorpay_gateway import RazorpayGateway
from services.flutterwave_gateway import FlutterwaveGateway
from services.paystack_gateway import PaystackGateway

router = APIRouter()

def get_payment_gateway(gateway: str = Query("stripe", enum=["stripe", "razorpay", "flutterwave", "paystack"])) -> PaymentGatewayAdapter:
    if gateway == "stripe":
        return StripeGateway(api_key="sk_test_..._mock")
    elif gateway == "razorpay":
        return RazorpayGateway(key_id="rzp_test_..._mock", key_secret="mock_secret")
    elif gateway == "flutterwave":
        return FlutterwaveGateway(secret_key="FLWSECK_TEST-...-X_mock")
    elif gateway == "paystack":
        return PaystackGateway(secret_key="sk_test_..._mock")

def get_billing_service(payment_gateway: PaymentGatewayAdapter = Depends(get_payment_gateway)) -> BillingService:
    return BillingService(payment_gateway)

@router.post("/change-subscription")
def change_subscription(new_plan: dict, old_plan: dict, billing_service: BillingService = Depends(get_billing_service)):
    # In a real app, user_id would come from the authenticated user
    user_id = "user_123"
    return billing_service.change_subscription(user_id, new_plan, old_plan)