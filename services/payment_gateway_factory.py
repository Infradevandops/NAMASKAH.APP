#!/usr/bin/env python3
"""
Payment Gateway Factory for namaskah
Manages multiple payment gateways with regional optimization and fallback support
"""
import os
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from services.payment_gateway_adapter import PaymentGatewayAdapter
from services.stripe_gateway import StripeGateway
from services.razorpay_gateway import RazorpayGateway
from services.flutterwave_gateway import FlutterwaveGateway
from services.paystack_gateway import PaystackGateway

logger = logging.getLogger(__name__)


class PaymentGatewayType(Enum):
    """Supported payment gateway types"""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class PaymentRegion(Enum):
    """Payment regions for gateway optimization"""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    AFRICA = "africa"
    LATIN_AMERICA = "latin_america"
    MIDDLE_EAST = "middle_east"


@dataclass
class GatewayConfig:
    """Payment gateway configuration"""
    gateway_type: PaymentGatewayType
    api_key: str
    secret_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    supported_regions: List[PaymentRegion] = None
    supported_currencies: List[str] = None
    max_amount: Optional[float] = None
    min_amount: Optional[float] = None


@dataclass
class PaymentAttempt:
    """Payment attempt result"""
    gateway_type: PaymentGatewayType
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None


class PaymentGatewayFactory:
    """Factory for managing multiple payment gateways"""
    
    def __init__(self):
        self.gateways: Dict[PaymentGatewayType, PaymentGatewayAdapter] = {}
        self.gateway_configs: Dict[PaymentGatewayType, GatewayConfig] = {}
        self.regional_preferences: Dict[PaymentRegion, List[PaymentGatewayType]] = {}
        
        # Initialize gateways from environment
        self._initialize_gateways()
        self._setup_regional_preferences()
    
    def _initialize_gateways(self):
        """Initialize payment gateways from environment configuration"""
        
        # Stripe configuration
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_key:
            try:
                self.gateways[PaymentGatewayType.STRIPE] = StripeGateway(stripe_key)
                self.gateway_configs[PaymentGatewayType.STRIPE] = GatewayConfig(
                    gateway_type=PaymentGatewayType.STRIPE,
                    api_key=stripe_key,
                    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
                    priority=1,
                    supported_regions=[
                        PaymentRegion.NORTH_AMERICA,
                        PaymentRegion.EUROPE,
                        PaymentRegion.ASIA_PACIFIC,
                        PaymentRegion.LATIN_AMERICA
                    ],
                    supported_currencies=["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
                    max_amount=999999.99
                )
                logger.info("✅ Stripe gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Stripe: {e}")
        
        # Razorpay configuration
        razorpay_key = os.getenv("RAZORPAY_KEY_ID")
        razorpay_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if razorpay_key and razorpay_secret:
            try:
                self.gateways[PaymentGatewayType.RAZORPAY] = RazorpayGateway(
                    razorpay_key, razorpay_secret
                )
                self.gateway_configs[PaymentGatewayType.RAZORPAY] = GatewayConfig(
                    gateway_type=PaymentGatewayType.RAZORPAY,
                    api_key=razorpay_key,
                    secret_key=razorpay_secret,
                    priority=1,
                    supported_regions=[PaymentRegion.ASIA_PACIFIC],
                    supported_currencies=["INR", "USD"],
                    max_amount=500000.00  # INR limit
                )
                logger.info("✅ Razorpay gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Razorpay: {e}")
        
        # Flutterwave configuration
        flutterwave_key = os.getenv("FLUTTERWAVE_SECRET_KEY")
        if flutterwave_key:
            try:
                self.gateways[PaymentGatewayType.FLUTTERWAVE] = FlutterwaveGateway(
                    flutterwave_key
                )
                self.gateway_configs[PaymentGatewayType.FLUTTERWAVE] = GatewayConfig(
                    gateway_type=PaymentGatewayType.FLUTTERWAVE,
                    api_key=flutterwave_key,
                    priority=1,
                    supported_regions=[PaymentRegion.AFRICA],
                    supported_currencies=["NGN", "KES", "GHS", "UGX", "USD"],
                    max_amount=1000000.00
                )
                logger.info("✅ Flutterwave gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Flutterwave: {e}")
        
        # Paystack configuration
        paystack_key = os.getenv("PAYSTACK_SECRET_KEY")
        if paystack_key:
            try:
                self.gateways[PaymentGatewayType.PAYSTACK] = PaystackGateway(
                    paystack_key
                )
                self.gateway_configs[PaymentGatewayType.PAYSTACK] = GatewayConfig(
                    gateway_type=PaymentGatewayType.PAYSTACK,
                    api_key=paystack_key,
                    priority=2,  # Lower priority than Flutterwave for Africa
                    supported_regions=[PaymentRegion.AFRICA],
                    supported_currencies=["NGN", "GHS", "ZAR", "USD"],
                    max_amount=500000.00
                )
                logger.info("✅ Paystack gateway initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Paystack: {e}")
        
        if not self.gateways:
            logger.warning("⚠️  No payment gateways initialized - payments will not work")
    
    def _setup_regional_preferences(self):
        """Setup regional gateway preferences"""
        self.regional_preferences = {
            PaymentRegion.NORTH_AMERICA: [
                PaymentGatewayType.STRIPE
            ],
            PaymentRegion.EUROPE: [
                PaymentGatewayType.STRIPE
            ],
            PaymentRegion.ASIA_PACIFIC: [
                PaymentGatewayType.RAZORPAY,
                PaymentGatewayType.STRIPE
            ],
            PaymentRegion.AFRICA: [
                PaymentGatewayType.FLUTTERWAVE,
                PaymentGatewayType.PAYSTACK,
                PaymentGatewayType.STRIPE
            ],
            PaymentRegion.LATIN_AMERICA: [
                PaymentGatewayType.STRIPE
            ],
            PaymentRegion.MIDDLE_EAST: [
                PaymentGatewayType.STRIPE
            ]
        }
    
    def get_optimal_gateway(
        self,
        region: Optional[PaymentRegion] = None,
        currency: str = "USD",
        amount: float = 0.0,
        country_code: Optional[str] = None
    ) -> Optional[PaymentGatewayAdapter]:
        """
        Get the optimal payment gateway for given parameters
        
        Args:
            region: Payment region
            currency: Transaction currency
            amount: Transaction amount
            country_code: ISO country code
            
        Returns:
            Optimal payment gateway or None if none available
        """
        # Determine region from country code if not provided
        if not region and country_code:
            region = self._get_region_from_country(country_code)
        
        # Get preferred gateways for region
        preferred_gateways = []
        if region and region in self.regional_preferences:
            preferred_gateways = self.regional_preferences[region]
        else:
            # Fallback to all available gateways
            preferred_gateways = list(self.gateways.keys())
        
        # Filter gateways by capabilities
        suitable_gateways = []
        for gateway_type in preferred_gateways:
            if gateway_type not in self.gateways:
                continue
                
            config = self.gateway_configs.get(gateway_type)
            if not config or not config.is_enabled:
                continue
            
            # Check currency support
            if config.supported_currencies and currency not in config.supported_currencies:
                continue
            
            # Check amount limits
            if config.max_amount and amount > config.max_amount:
                continue
            
            if config.min_amount and amount < config.min_amount:
                continue
            
            suitable_gateways.append((gateway_type, config.priority))
        
        # Sort by priority and return the best gateway
        if suitable_gateways:
            suitable_gateways.sort(key=lambda x: x[1])  # Sort by priority
            best_gateway_type = suitable_gateways[0][0]
            return self.gateways[best_gateway_type]
        
        return None
    
    def _get_region_from_country(self, country_code: str) -> PaymentRegion:
        """Map country code to payment region"""
        country_region_map = {
            # North America
            "US": PaymentRegion.NORTH_AMERICA,
            "CA": PaymentRegion.NORTH_AMERICA,
            "MX": PaymentRegion.NORTH_AMERICA,
            
            # Europe
            "GB": PaymentRegion.EUROPE,
            "DE": PaymentRegion.EUROPE,
            "FR": PaymentRegion.EUROPE,
            "IT": PaymentRegion.EUROPE,
            "ES": PaymentRegion.EUROPE,
            "NL": PaymentRegion.EUROPE,
            "SE": PaymentRegion.EUROPE,
            "NO": PaymentRegion.EUROPE,
            "DK": PaymentRegion.EUROPE,
            "FI": PaymentRegion.EUROPE,
            
            # Asia Pacific
            "IN": PaymentRegion.ASIA_PACIFIC,
            "CN": PaymentRegion.ASIA_PACIFIC,
            "JP": PaymentRegion.ASIA_PACIFIC,
            "KR": PaymentRegion.ASIA_PACIFIC,
            "AU": PaymentRegion.ASIA_PACIFIC,
            "NZ": PaymentRegion.ASIA_PACIFIC,
            "SG": PaymentRegion.ASIA_PACIFIC,
            "MY": PaymentRegion.ASIA_PACIFIC,
            "TH": PaymentRegion.ASIA_PACIFIC,
            "PH": PaymentRegion.ASIA_PACIFIC,
            "ID": PaymentRegion.ASIA_PACIFIC,
            "VN": PaymentRegion.ASIA_PACIFIC,
            
            # Africa
            "NG": PaymentRegion.AFRICA,
            "KE": PaymentRegion.AFRICA,
            "GH": PaymentRegion.AFRICA,
            "UG": PaymentRegion.AFRICA,
            "TZ": PaymentRegion.AFRICA,
            "ZA": PaymentRegion.AFRICA,
            "EG": PaymentRegion.AFRICA,
            "MA": PaymentRegion.AFRICA,
            
            # Latin America
            "BR": PaymentRegion.LATIN_AMERICA,
            "AR": PaymentRegion.LATIN_AMERICA,
            "CL": PaymentRegion.LATIN_AMERICA,
            "CO": PaymentRegion.LATIN_AMERICA,
            "PE": PaymentRegion.LATIN_AMERICA,
            "VE": PaymentRegion.LATIN_AMERICA,
            
            # Middle East
            "AE": PaymentRegion.MIDDLE_EAST,
            "SA": PaymentRegion.MIDDLE_EAST,
            "IL": PaymentRegion.MIDDLE_EAST,
            "TR": PaymentRegion.MIDDLE_EAST,
        }
        
        return country_region_map.get(country_code.upper(), PaymentRegion.NORTH_AMERICA)
    
    def process_payment_with_fallback(
        self,
        amount: float,
        currency: str,
        payment_method_id: str,
        description: str,
        region: Optional[PaymentRegion] = None,
        country_code: Optional[str] = None,
        max_attempts: int = 3
    ) -> List[PaymentAttempt]:
        """
        Process payment with automatic fallback to other gateways
        
        Args:
            amount: Payment amount
            currency: Currency code
            payment_method_id: Payment method identifier
            description: Payment description
            region: Payment region
            country_code: Country code
            max_attempts: Maximum number of gateway attempts
            
        Returns:
            List of payment attempts
        """
        attempts = []
        
        # Get ordered list of gateways to try
        gateways_to_try = self._get_fallback_gateways(
            region, currency, amount, country_code, max_attempts
        )
        
        for gateway_type in gateways_to_try:
            gateway = self.gateways.get(gateway_type)
            if not gateway:
                continue
            
            try:
                import time
                start_time = time.time()
                
                # Attempt payment
                result = gateway.create_charge(
                    amount=int(amount * 100),  # Convert to cents
                    currency=currency,
                    source=payment_method_id,
                    description=description
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                # Check if payment succeeded
                if "error" not in result:
                    attempts.append(PaymentAttempt(
                        gateway_type=gateway_type,
                        success=True,
                        result=result,
                        processing_time_ms=processing_time
                    ))
                    logger.info(f"✅ Payment successful via {gateway_type.value}")
                    break
                else:
                    attempts.append(PaymentAttempt(
                        gateway_type=gateway_type,
                        success=False,
                        result=result,
                        error=result.get("error"),
                        processing_time_ms=processing_time
                    ))
                    logger.warning(f"⚠️  Payment failed via {gateway_type.value}: {result.get('error')}")
                
            except Exception as e:
                attempts.append(PaymentAttempt(
                    gateway_type=gateway_type,
                    success=False,
                    result={},
                    error=str(e)
                ))
                logger.error(f"❌ Payment error via {gateway_type.value}: {e}")
        
        return attempts
    
    def _get_fallback_gateways(
        self,
        region: Optional[PaymentRegion],
        currency: str,
        amount: float,
        country_code: Optional[str],
        max_attempts: int
    ) -> List[PaymentGatewayType]:
        """Get ordered list of gateways for fallback attempts"""
        
        # Start with optimal gateway
        optimal_gateway = self.get_optimal_gateway(region, currency, amount, country_code)
        gateways_to_try = []
        
        if optimal_gateway:
            # Find the gateway type
            for gateway_type, gateway in self.gateways.items():
                if gateway == optimal_gateway:
                    gateways_to_try.append(gateway_type)
                    break
        
        # Add other suitable gateways as fallbacks
        for gateway_type, config in self.gateway_configs.items():
            if gateway_type in gateways_to_try:
                continue
            
            if not config.is_enabled:
                continue
            
            # Check basic compatibility
            if config.supported_currencies and currency not in config.supported_currencies:
                continue
            
            if config.max_amount and amount > config.max_amount:
                continue
            
            gateways_to_try.append(gateway_type)
        
        # Limit to max attempts
        return gateways_to_try[:max_attempts]
    
    def get_gateway_status(self) -> Dict[str, Any]:
        """Get status of all configured gateways"""
        status = {
            "total_gateways": len(self.gateways),
            "enabled_gateways": sum(1 for config in self.gateway_configs.values() if config.is_enabled),
            "gateways": {}
        }
        
        for gateway_type, config in self.gateway_configs.items():
            gateway_status = {
                "enabled": config.is_enabled,
                "priority": config.priority,
                "supported_regions": [r.value for r in config.supported_regions] if config.supported_regions else [],
                "supported_currencies": config.supported_currencies or [],
                "limits": {
                    "max_amount": config.max_amount,
                    "min_amount": config.min_amount
                }
            }
            
            # Test gateway connectivity
            try:
                gateway = self.gateways.get(gateway_type)
                if gateway:
                    # Simple connectivity test (this would be gateway-specific)
                    gateway_status["connectivity"] = "healthy"
                else:
                    gateway_status["connectivity"] = "not_initialized"
            except Exception as e:
                gateway_status["connectivity"] = f"error: {str(e)}"
            
            status["gateways"][gateway_type.value] = gateway_status
        
        return status
    
    def update_gateway_config(
        self,
        gateway_type: PaymentGatewayType,
        **config_updates
    ) -> bool:
        """Update gateway configuration"""
        if gateway_type not in self.gateway_configs:
            return False
        
        config = self.gateway_configs[gateway_type]
        
        # Update allowed fields
        allowed_updates = ['is_enabled', 'priority', 'max_amount', 'min_amount']
        for key, value in config_updates.items():
            if key in allowed_updates:
                setattr(config, key, value)
        
        logger.info(f"Updated configuration for {gateway_type.value}")
        return True


# Global factory instance
payment_gateway_factory = PaymentGatewayFactory()