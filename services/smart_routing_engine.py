#!/usr/bin/env python3
"""
Smart Routing Engine for namaskah Communication Platform
Provides intelligent number selection, cost optimization, and geographic routing
"""
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import phonenumbers
from phonenumbers import carrier, geocoder

from clients.enhanced_twilio_client import EnhancedTwilioClient

logger = logging.getLogger(__name__)


@dataclass
class CountryInfo:
    """Information about a country for routing calculations"""

    code: str
    name: str
    continent: str
    latitude: float
    longitude: float
    calling_code: str
    currency: str
    timezone_offset: float


@dataclass
class NumberOption:
    """Represents a phone number option with routing information"""

    phone_number: str
    country_code: str
    country_name: str
    area_code: Optional[str]
    monthly_cost: float
    sms_cost: float
    voice_cost: float
    distance_km: float
    delivery_score: float
    total_score: float
    capabilities: Dict[str, bool]
    provider: str = "twilio"


@dataclass
class RoutingRecommendation:
    """Complete routing recommendation with multiple options"""

    destination_number: str
    destination_country: str
    primary_option: NumberOption
    alternative_options: List[NumberOption]
    cost_savings: float
    delivery_improvement: float
    recommendation_reason: str


class SmartRoutingEngine:
    """
    Smart routing engine for optimal number selection and cost calculation
    """

    def __init__(self, twilio_client: EnhancedTwilioClient = None):
        """
        Initialize the smart routing engine

        Args:
            twilio_client: Enhanced Twilio client for number operations
        """
        self.twilio_client = twilio_client
        self.country_data = self._load_country_data()
        self.cost_matrix = self._load_cost_matrix()

        logger.info("Smart routing engine initialized successfully")

    def _load_country_data(self) -> Dict[str, CountryInfo]:
        """
        Load country information for routing calculations

        Returns:
            Dictionary mapping country codes to CountryInfo objects
        """
        # Comprehensive country data with geographic and telecom information
        countries = {
            "US": CountryInfo(
                "US",
                "United States",
                "North America",
                39.8283,
                -98.5795,
                "+1",
                "USD",
                -5.0,
            ),
            "CA": CountryInfo(
                "CA", "Canada", "North America", 56.1304, -106.3468, "+1", "CAD", -5.0
            ),
            "GB": CountryInfo(
                "GB", "United Kingdom", "Europe", 55.3781, -3.4360, "+44", "GBP", 0.0
            ),
            "DE": CountryInfo(
                "DE", "Germany", "Europe", 51.1657, 10.4515, "+49", "EUR", 1.0
            ),
            "FR": CountryInfo(
                "FR", "France", "Europe", 46.2276, 2.2137, "+33", "EUR", 1.0
            ),
            "IT": CountryInfo(
                "IT", "Italy", "Europe", 41.8719, 12.5674, "+39", "EUR", 1.0
            ),
            "ES": CountryInfo(
                "ES", "Spain", "Europe", 40.4637, -3.7492, "+34", "EUR", 1.0
            ),
            "NL": CountryInfo(
                "NL", "Netherlands", "Europe", 52.1326, 5.2913, "+31", "EUR", 1.0
            ),
            "AU": CountryInfo(
                "AU", "Australia", "Oceania", -25.2744, 133.7751, "+61", "AUD", 10.0
            ),
            "JP": CountryInfo(
                "JP", "Japan", "Asia", 36.2048, 138.2529, "+81", "JPY", 9.0
            ),
            "CN": CountryInfo(
                "CN", "China", "Asia", 35.8617, 104.1954, "+86", "CNY", 8.0
            ),
            "IN": CountryInfo(
                "IN", "India", "Asia", 20.5937, 78.9629, "+91", "INR", 5.5
            ),
            "BR": CountryInfo(
                "BR", "Brazil", "South America", -14.2350, -51.9253, "+55", "BRL", -3.0
            ),
            "MX": CountryInfo(
                "MX", "Mexico", "North America", 23.6345, -102.5528, "+52", "MXN", -6.0
            ),
            "AR": CountryInfo(
                "AR",
                "Argentina",
                "South America",
                -38.4161,
                -63.6167,
                "+54",
                "ARS",
                -3.0,
            ),
            "ZA": CountryInfo(
                "ZA", "South Africa", "Africa", -30.5595, 22.9375, "+27", "ZAR", 2.0
            ),
            "NG": CountryInfo(
                "NG", "Nigeria", "Africa", 9.0820, 8.6753, "+234", "NGN", 1.0
            ),
            "EG": CountryInfo(
                "EG", "Egypt", "Africa", 26.8206, 30.8025, "+20", "EGP", 2.0
            ),
            "RU": CountryInfo(
                "RU", "Russia", "Europe/Asia", 61.5240, 105.3188, "+7", "RUB", 3.0
            ),
            "KR": CountryInfo(
                "KR", "South Korea", "Asia", 35.9078, 127.7669, "+82", "KRW", 9.0
            ),
            "SG": CountryInfo(
                "SG", "Singapore", "Asia", 1.3521, 103.8198, "+65", "SGD", 8.0
            ),
            "HK": CountryInfo(
                "HK", "Hong Kong", "Asia", 22.3193, 114.1694, "+852", "HKD", 8.0
            ),
            "TH": CountryInfo(
                "TH", "Thailand", "Asia", 15.8700, 100.9925, "+66", "THB", 7.0
            ),
            "MY": CountryInfo(
                "MY", "Malaysia", "Asia", 4.2105, 101.9758, "+60", "MYR", 8.0
            ),
            "ID": CountryInfo(
                "ID", "Indonesia", "Asia", -0.7893, 113.9213, "+62", "IDR", 7.0
            ),
            "PH": CountryInfo(
                "PH", "Philippines", "Asia", 12.8797, 121.7740, "+63", "PHP", 8.0
            ),
            "VN": CountryInfo(
                "VN", "Vietnam", "Asia", 14.0583, 108.2772, "+84", "VND", 7.0
            ),
            "TR": CountryInfo(
                "TR", "Turkey", "Europe/Asia", 38.9637, 35.2433, "+90", "TRY", 3.0
            ),
            "SA": CountryInfo(
                "SA", "Saudi Arabia", "Asia", 23.8859, 45.0792, "+966", "SAR", 3.0
            ),
            "AE": CountryInfo(
                "AE",
                "United Arab Emirates",
                "Asia",
                23.4241,
                53.8478,
                "+971",
                "AED",
                4.0,
            ),
            "IL": CountryInfo(
                "IL", "Israel", "Asia", 31.0461, 34.8516, "+972", "ILS", 2.0
            ),
            "SE": CountryInfo(
                "SE", "Sweden", "Europe", 60.1282, 18.6435, "+46", "SEK", 1.0
            ),
            "NO": CountryInfo(
                "NO", "Norway", "Europe", 60.4720, 8.4689, "+47", "NOK", 1.0
            ),
            "DK": CountryInfo(
                "DK", "Denmark", "Europe", 56.2639, 9.5018, "+45", "DKK", 1.0
            ),
            "FI": CountryInfo(
                "FI", "Finland", "Europe", 61.9241, 25.7482, "+358", "EUR", 2.0
            ),
            "CH": CountryInfo(
                "CH", "Switzerland", "Europe", 46.8182, 8.2275, "+41", "CHF", 1.0
            ),
            "AT": CountryInfo(
                "AT", "Austria", "Europe", 47.5162, 14.5501, "+43", "EUR", 1.0
            ),
            "BE": CountryInfo(
                "BE", "Belgium", "Europe", 50.5039, 4.4699, "+32", "EUR", 1.0
            ),
            "PT": CountryInfo(
                "PT", "Portugal", "Europe", 39.3999, -8.2245, "+351", "EUR", 0.0
            ),
            "IE": CountryInfo(
                "IE", "Ireland", "Europe", 53.4129, -8.2439, "+353", "EUR", 0.0
            ),
            "PL": CountryInfo(
                "PL", "Poland", "Europe", 51.9194, 19.1451, "+48", "PLN", 1.0
            ),
            "CZ": CountryInfo(
                "CZ", "Czech Republic", "Europe", 49.8175, 15.4730, "+420", "CZK", 1.0
            ),
            "HU": CountryInfo(
                "HU", "Hungary", "Europe", 47.1625, 19.5033, "+36", "HUF", 1.0
            ),
            "RO": CountryInfo(
                "RO", "Romania", "Europe", 45.9432, 24.9668, "+40", "RON", 2.0
            ),
            "BG": CountryInfo(
                "BG", "Bulgaria", "Europe", 42.7339, 25.4858, "+359", "BGN", 2.0
            ),
            "GR": CountryInfo(
                "GR", "Greece", "Europe", 39.0742, 21.8243, "+30", "EUR", 2.0
            ),
            "HR": CountryInfo(
                "HR", "Croatia", "Europe", 45.1000, 15.2000, "+385", "HRK", 1.0
            ),
            "SI": CountryInfo(
                "SI", "Slovenia", "Europe", 46.1512, 14.9955, "+386", "EUR", 1.0
            ),
            "SK": CountryInfo(
                "SK", "Slovakia", "Europe", 48.6690, 19.6990, "+421", "EUR", 1.0
            ),
            "LT": CountryInfo(
                "LT", "Lithuania", "Europe", 55.1694, 23.8813, "+370", "EUR", 2.0
            ),
            "LV": CountryInfo(
                "LV", "Latvia", "Europe", 56.8796, 24.6032, "+371", "EUR", 2.0
            ),
            "EE": CountryInfo(
                "EE", "Estonia", "Europe", 58.5953, 25.0136, "+372", "EUR", 2.0
            ),
        }

        logger.info(f"Loaded country data for {len(countries)} countries")
        return countries

    def _load_cost_matrix(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Load cost matrix for SMS and voice calls between countries

        Returns:
            Nested dictionary with costs: cost_matrix[from_country][to_country][service_type]
        """
        # Simplified cost matrix - in production, this would be loaded from a database
        # or external pricing API
        base_costs = {
            "domestic_sms": 0.0075,  # $0.0075 per SMS domestically
            "domestic_voice": 0.02,  # $0.02 per minute domestically
            "international_sms": 0.05,  # $0.05 per SMS internationally
            "international_voice": 0.15,  # $0.15 per minute internationally
            "premium_sms": 0.10,  # $0.10 per SMS to premium destinations
            "premium_voice": 0.30,  # $0.30 per minute to premium destinations
        }

        # Premium destinations (higher costs)
        premium_countries = {"CN", "RU", "IN", "NG", "EG", "SA", "AE"}

        cost_matrix = {}

        for from_country in self.country_data:
            cost_matrix[from_country] = {}

            for to_country in self.country_data:
                if from_country == to_country:
                    # Domestic rates
                    cost_matrix[from_country][to_country] = {
                        "sms": base_costs["domestic_sms"],
                        "voice": base_costs["domestic_voice"],
                    }
                elif to_country in premium_countries:
                    # Premium international rates
                    cost_matrix[from_country][to_country] = {
                        "sms": base_costs["premium_sms"],
                        "voice": base_costs["premium_voice"],
                    }
                else:
                    # Standard international rates
                    cost_matrix[from_country][to_country] = {
                        "sms": base_costs["international_sms"],
                        "voice": base_costs["international_voice"],
                    }

        logger.info("Loaded cost matrix for international routing")
        return cost_matrix

    def calculate_distance(self, country1: str, country2: str) -> float:
        """
        Calculate distance between two countries using their geographic centers

        Args:
            country1: First country code
            country2: Second country code

        Returns:
            Distance in kilometers
        """
        if country1 not in self.country_data or country2 not in self.country_data:
            return float("inf")

        if country1 == country2:
            return 0.0

        # Get coordinates
        c1 = self.country_data[country1]
        c2 = self.country_data[country2]

        # Haversine formula for great circle distance
        lat1, lon1 = math.radians(c1.latitude), math.radians(c1.longitude)
        lat2, lon2 = math.radians(c2.latitude), math.radians(c2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        earth_radius = 6371.0
        distance = earth_radius * c

        return distance

    def get_country_from_number(self, phone_number: str) -> Optional[str]:
        """
        Extract country code from phone number

        Args:
            phone_number: Phone number to analyze

        Returns:
            ISO country code or None if not found
        """
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            country_code = phonenumbers.region_code_for_number(parsed_number)
            return country_code
        except phonenumbers.NumberParseException:
            logger.warning(f"Could not parse phone number: {phone_number}")
            return None

    def get_closest_countries(
        self, target_country: str, limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get countries closest to the target country

        Args:
            target_country: Target country code
            limit: Maximum number of countries to return

        Returns:
            List of (country_code, distance) tuples sorted by distance
        """
        if target_country not in self.country_data:
            return []

        distances = []
        for country_code in self.country_data:
            if country_code != target_country:
                distance = self.calculate_distance(target_country, country_code)
                distances.append((country_code, distance))

        # Sort by distance and return top results
        distances.sort(key=lambda x: x[1])
        return distances[:limit]

    def calculate_delivery_score(self, from_country: str, to_country: str) -> float:
        """
        Calculate delivery score based on geographic and network factors

        Args:
            from_country: Sender country
            to_country: Recipient country

        Returns:
            Delivery score (0.0 to 1.0, higher is better)
        """
        if from_country == to_country:
            return 1.0  # Perfect score for domestic

        # Base score for international
        base_score = 0.7

        # Distance factor (closer is better)
        distance = self.calculate_distance(from_country, to_country)
        if distance == float("inf"):
            return 0.1

        # Normalize distance (assume max useful distance is 20,000 km)
        distance_factor = max(0, 1 - (distance / 20000))

        # Continent bonus (same continent gets bonus)
        continent_bonus = 0.0
        if from_country in self.country_data and to_country in self.country_data:
            if (
                self.country_data[from_country].continent
                == self.country_data[to_country].continent
            ):
                continent_bonus = 0.1

        # Calculate final score
        final_score = base_score + (distance_factor * 0.2) + continent_bonus
        return min(1.0, max(0.0, final_score))

    def calculate_cost_comparison(
        self,
        from_country: str,
        to_country: str,
        message_count: int = 1,
        call_minutes: int = 0,
    ) -> Dict[str, float]:
        """
        Calculate cost comparison for different routing options

        Args:
            from_country: Sender country
            to_country: Recipient country
            message_count: Number of SMS messages
            call_minutes: Number of voice call minutes

        Returns:
            Dictionary with cost breakdown
        """
        if (
            from_country not in self.cost_matrix
            or to_country not in self.cost_matrix[from_country]
        ):
            return {"sms_cost": 0.0, "voice_cost": 0.0, "total_cost": 0.0}

        costs = self.cost_matrix[from_country][to_country]

        sms_cost = costs["sms"] * message_count
        voice_cost = costs["voice"] * call_minutes
        total_cost = sms_cost + voice_cost

        return {
            "sms_cost": sms_cost,
            "voice_cost": voice_cost,
            "total_cost": total_cost,
            "per_sms": costs["sms"],
            "per_minute": costs["voice"],
        }

    async def suggest_optimal_numbers(
        self,
        destination_number: str,
        user_numbers: List[str] = None,
        message_count: int = 1,
        call_minutes: int = 0,
    ) -> RoutingRecommendation:
        """
        Suggest optimal phone numbers for communication with destination

        Args:
            destination_number: Target phone number
            user_numbers: List of user's existing numbers
            message_count: Expected number of SMS messages
            call_minutes: Expected call duration in minutes

        Returns:
            RoutingRecommendation with optimal choices
        """
        try:
            # Get destination country
            dest_country = self.get_country_from_number(destination_number)
            if not dest_country:
                raise ValueError(
                    f"Could not determine country for {destination_number}"
                )

            options = []

            # Evaluate user's existing numbers
            if user_numbers:
                for number in user_numbers:
                    from_country = self.get_country_from_number(number)
                    if from_country:
                        option = await self._evaluate_number_option(
                            number,
                            from_country,
                            dest_country,
                            message_count,
                            call_minutes,
                            is_owned=True,
                        )
                        if option:
                            options.append(option)

            # Get closest countries for potential new numbers
            closest_countries = self.get_closest_countries(dest_country, limit=3)

            # Add domestic option (same country as destination)
            if dest_country not in [opt.country_code for opt in options]:
                domestic_option = await self._create_hypothetical_option(
                    dest_country, dest_country, message_count, call_minutes
                )
                if domestic_option:
                    options.append(domestic_option)

            # Add closest country options
            for country_code, distance in closest_countries:
                if country_code not in [opt.country_code for opt in options]:
                    option = await self._create_hypothetical_option(
                        country_code, dest_country, message_count, call_minutes
                    )
                    if option:
                        options.append(option)

            # Sort options by total score (higher is better)
            options.sort(key=lambda x: x.total_score, reverse=True)

            if not options:
                raise ValueError("No routing options available")

            # Create recommendation
            primary_option = options[0]
            alternative_options = options[1:5]  # Top 4 alternatives

            # Calculate savings compared to worst option
            worst_cost = max(
                opt.monthly_cost
                + (opt.sms_cost * message_count)
                + (opt.voice_cost * call_minutes)
                for opt in options
            )
            best_cost = (
                primary_option.monthly_cost
                + (primary_option.sms_cost * message_count)
                + (primary_option.voice_cost * call_minutes)
            )
            cost_savings = worst_cost - best_cost

            # Calculate delivery improvement
            worst_delivery = min(opt.delivery_score for opt in options)
            delivery_improvement = primary_option.delivery_score - worst_delivery

            # Generate recommendation reason
            reason = self._generate_recommendation_reason(
                primary_option, dest_country, cost_savings, delivery_improvement
            )

            recommendation = RoutingRecommendation(
                destination_number=destination_number,
                destination_country=dest_country,
                primary_option=primary_option,
                alternative_options=alternative_options,
                cost_savings=cost_savings,
                delivery_improvement=delivery_improvement,
                recommendation_reason=reason,
            )

            logger.info(f"Generated routing recommendation for {destination_number}")
            return recommendation

        except Exception as e:
            logger.error(f"Error generating routing recommendation: {e}")
            raise

    async def _evaluate_number_option(
        self,
        phone_number: str,
        from_country: str,
        to_country: str,
        message_count: int,
        call_minutes: int,
        is_owned: bool = False,
    ) -> Optional[NumberOption]:
        """
        Evaluate a specific phone number as a routing option
        """
        try:
            # Calculate costs
            cost_info = self.calculate_cost_comparison(
                from_country, to_country, message_count, call_minutes
            )

            # Calculate delivery score
            delivery_score = self.calculate_delivery_score(from_country, to_country)

            # Calculate distance
            distance = self.calculate_distance(from_country, to_country)

            # Monthly cost (0 if already owned)
            monthly_cost = 0.0 if is_owned else 1.0  # $1/month for new numbers

            # Calculate total score (weighted combination of factors)
            cost_score = max(
                0, 1 - (cost_info["per_sms"] / 0.10)
            )  # Normalize to $0.10 max
            distance_score = max(0, 1 - (distance / 20000))  # Normalize to 20,000km max
            ownership_bonus = 0.2 if is_owned else 0.0

            total_score = (
                delivery_score * 0.4
                + cost_score * 0.3
                + distance_score * 0.2
                + ownership_bonus * 0.1
            )

            country_name = self.country_data.get(
                from_country, CountryInfo("", "", "", 0, 0, "", "", 0)
            ).name

            option = NumberOption(
                phone_number=phone_number,
                country_code=from_country,
                country_name=country_name,
                area_code=None,  # Would extract from number in production
                monthly_cost=monthly_cost,
                sms_cost=cost_info["per_sms"],
                voice_cost=cost_info["per_minute"],
                distance_km=distance,
                delivery_score=delivery_score,
                total_score=total_score,
                capabilities={"sms": True, "voice": True, "mms": True},
                provider="twilio",
            )

            return option

        except Exception as e:
            logger.error(f"Error evaluating number option {phone_number}: {e}")
            return None

    async def _create_hypothetical_option(
        self, from_country: str, to_country: str, message_count: int, call_minutes: int
    ) -> Optional[NumberOption]:
        """
        Create a hypothetical number option for a country
        """
        try:
            # Generate a hypothetical number for the country
            country_info = self.country_data.get(from_country)
            if not country_info:
                return None

            # Create a sample number (in production, would query Twilio for available numbers)
            sample_number = f"{country_info.calling_code}555000001"

            return await self._evaluate_number_option(
                sample_number,
                from_country,
                to_country,
                message_count,
                call_minutes,
                is_owned=False,
            )

        except Exception as e:
            logger.error(f"Error creating hypothetical option for {from_country}: {e}")
            return None

    def _generate_recommendation_reason(
        self,
        option: NumberOption,
        dest_country: str,
        cost_savings: float,
        delivery_improvement: float,
    ) -> str:
        """
        Generate human-readable recommendation reason
        """
        reasons = []

        if option.country_code == dest_country:
            reasons.append("domestic number provides best delivery rates")
        elif option.distance_km < 2000:
            reasons.append("geographically close for optimal routing")

        if cost_savings > 0.01:
            reasons.append(f"saves ${cost_savings:.3f} compared to alternatives")

        if delivery_improvement > 0.1:
            reasons.append(f"improves delivery score by {delivery_improvement:.1%}")

        if option.monthly_cost == 0:
            reasons.append("uses existing owned number")

        if not reasons:
            reasons.append("balanced cost and delivery performance")

        return f"Recommended because it {', '.join(reasons)}"

    async def get_routing_analytics(
        self, user_numbers: List[str], recent_destinations: List[str]
    ) -> Dict[str, Any]:
        """
        Generate routing analytics and optimization suggestions

        Args:
            user_numbers: List of user's phone numbers
            recent_destinations: List of recent destination numbers

        Returns:
            Analytics data with optimization suggestions
        """
        try:
            analytics = {
                "user_numbers": len(user_numbers),
                "countries_covered": set(),
                "recent_destinations": len(recent_destinations),
                "destination_countries": set(),
                "optimization_opportunities": [],
                "cost_analysis": {},
                "coverage_gaps": [],
            }

            # Analyze user's number coverage
            for number in user_numbers:
                country = self.get_country_from_number(number)
                if country:
                    analytics["countries_covered"].add(country)

            # Analyze destination patterns
            destination_countries = {}
            for dest in recent_destinations:
                country = self.get_country_from_number(dest)
                if country:
                    analytics["destination_countries"].add(country)
                    destination_countries[country] = (
                        destination_countries.get(country, 0) + 1
                    )

            # Find optimization opportunities
            for dest_country, frequency in destination_countries.items():
                if (
                    dest_country not in analytics["countries_covered"]
                    and frequency >= 3
                ):
                    # Suggest getting a local number for frequently contacted countries
                    country_name = self.country_data.get(
                        dest_country, CountryInfo("", "", "", 0, 0, "", "", 0)
                    ).name
                    analytics["optimization_opportunities"].append(
                        {
                            "type": "local_number_suggestion",
                            "country": dest_country,
                            "country_name": country_name,
                            "frequency": frequency,
                            "potential_savings": frequency
                            * 0.04,  # Estimated savings per message
                            "reason": f"You frequently contact {country_name} ({frequency} times). A local number could reduce costs.",
                        }
                    )

            # Convert sets to lists for JSON serialization
            analytics["countries_covered"] = list(analytics["countries_covered"])
            analytics["destination_countries"] = list(
                analytics["destination_countries"]
            )

            logger.info("Generated routing analytics")
            return analytics

        except Exception as e:
            logger.error(f"Error generating routing analytics: {e}")
            raise


# Factory function
def create_smart_routing_engine(
    twilio_client: EnhancedTwilioClient = None,
) -> SmartRoutingEngine:
    """
    Factory function to create smart routing engine

    Args:
        twilio_client: Enhanced Twilio client instance

    Returns:
        SmartRoutingEngine instance
    """
    try:
        return SmartRoutingEngine(twilio_client)
    except Exception as e:
        logger.error(f"Failed to create smart routing engine: {e}")
        raise


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_routing_engine():
        engine = SmartRoutingEngine()

        try:
            # Test distance calculation
            distance = engine.calculate_distance("US", "CA")
            print(f"Distance US to CA: {distance:.2f} km")

            # Test country detection
            country = engine.get_country_from_number("+1234567890")
            print(f"Country for +1234567890: {country}")

            # Test closest countries
            closest = engine.get_closest_countries("US", limit=3)
            print(f"Closest to US: {closest}")

            # Test cost calculation
            costs = engine.calculate_cost_comparison("US", "GB", message_count=10)
            print(f"Cost US to GB (10 SMS): {costs}")

            # Test routing recommendation
            recommendation = await engine.suggest_optimal_numbers(
                "+447700000000",  # UK number
                user_numbers=["+1234567890"],  # US number
                message_count=5,
            )
            print(f"Recommendation: {recommendation.recommendation_reason}")

        except Exception as e:
            print(f"Error: {e}")

    # Run test
    asyncio.run(test_routing_engine())
