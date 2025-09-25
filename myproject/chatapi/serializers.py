from rest_framework import serializers
from .models import Message, Conversation, TrainingData

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'is_user', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'session_id', 'created_at', 'messages']

class TrainingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingData
        fields = ['id', 'question', 'answer', 'question_type', 'created_at']