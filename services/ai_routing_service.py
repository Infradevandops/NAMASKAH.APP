import json
from models.routing_models import RoutingRule, RoutingHistory
from core.database import SessionLocal
from clients.groq_client import GroqClient

class AIRoutingService:
    def __init__(self):
        self.db = SessionLocal()
        self.groq_client = GroqClient()

    def create_routing_rule(self, name: str, condition: dict, action: dict, priority: int = 0):
        rule = RoutingRule(
            name=name,
            condition=json.dumps(condition),
            action=json.dumps(action),
            priority=priority
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_active_rules(self):
        return self.db.query(RoutingRule).filter(RoutingRule.is_active == True).order_by(RoutingRule.priority.desc()).all()

    def evaluate_message(self, message_content: str, sender_info: dict):
        rules = self.get_active_rules()
        for rule in rules:
            condition = json.loads(rule.condition)
            if self._matches_condition(message_content, sender_info, condition):
                action = json.loads(rule.action)
                confidence = self._calculate_confidence(message_content, condition)
                return {
                    'rule': rule,
                    'action': action,
                    'confidence': confidence
                }
        return None

    def _matches_condition(self, message: str, sender: dict, condition: dict):
        # Simple condition matching - can be extended with AI
        if 'keywords' in condition:
            keywords = condition['keywords']
            return any(keyword.lower() in message.lower() for keyword in keywords)
        if 'sender_type' in condition:
            return sender.get('type') == condition['sender_type']
        return False

    def _calculate_confidence(self, message: str, condition: dict):
        # Use AI to calculate confidence score
        prompt = f"Rate the confidence (0-1) that this message matches the condition: {condition}. Message: {message}"
        response = self.groq_client.generate_response(prompt)
        try:
            return float(response.strip())
        except:
            return 0.5

    def log_routing_decision(self, message_id: int, route_taken: str, rule_id: int = None, confidence: float = None):
        history = RoutingHistory(
            message_id=message_id,
            rule_id=rule_id,
            route_taken=route_taken,
            confidence_score=confidence
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history
