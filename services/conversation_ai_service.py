import json
from models.routing_models import ConversationIntelligence
from core.database import SessionLocal
from clients.groq_client import GroqClient

class ConversationAIService:
    def __init__(self):
        self.db = SessionLocal()
        self.groq_client = GroqClient()

    def analyze_conversation(self, conversation_id: int, messages: list):
        # Extract conversation text
        conversation_text = " ".join([msg.get('content', '') for msg in messages])

        # Analyze sentiment
        sentiment_score = self._analyze_sentiment(conversation_text)

        # Detect intent
        intent = self._detect_intent(conversation_text)

        # Extract keywords
        keywords = self._extract_keywords(conversation_text)

        # Generate summary
        summary = self._generate_summary(conversation_text)

        # Save intelligence
        intelligence = ConversationIntelligence(
            conversation_id=conversation_id,
            sentiment_score=sentiment_score,
            intent=intent,
            keywords=json.dumps(keywords),
            summary=summary
        )
        self.db.add(intelligence)
        self.db.commit()
        self.db.refresh(intelligence)
        return intelligence

    def _analyze_sentiment(self, text: str):
        prompt = f"Analyze the sentiment of this conversation and return a score between -1 (very negative) and 1 (very positive): {text[:500]}"
        response = self.groq_client.generate_response(prompt)
        try:
            return float(response.strip())
        except:
            return 0.0

    def _detect_intent(self, text: str):
        prompt = f"Detect the main intent of this conversation (e.g., support, sales, complaint, inquiry): {text[:500]}"
        response = self.groq_client.generate_response(prompt)
        return response.strip()

    def _extract_keywords(self, text: str):
        prompt = f"Extract the top 5 keywords from this conversation: {text[:500]}"
        response = self.groq_client.generate_response(prompt)
        keywords = [k.strip() for k in response.split(',') if k.strip()]
        return keywords[:5]

    def _generate_summary(self, text: str):
        prompt = f"Summarize this conversation in 2-3 sentences: {text[:1000]}"
        response = self.groq_client.generate_response(prompt)
        return response.strip()

    def get_conversation_intelligence(self, conversation_id: int):
        return self.db.query(ConversationIntelligence).filter(ConversationIntelligence.conversation_id == conversation_id).all()
