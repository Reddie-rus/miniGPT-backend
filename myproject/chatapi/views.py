import requests
import base64
import uuid
import urllib3
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import render
from .models import Conversation, Message, TrainingData
from .serializers import ConversationSerializer, MessageSerializer, TrainingDataSerializer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def chat_view(request):
    return render(request, 'chat.html')

class BaseGigaChatView(APIView):
    
    def get_access_token(self):
        """Получение access token для GigaChat API"""
        authorization_key = "MDE5OTY4MTEtY2QzNi03NDU5LWJmYzMtZmIzMmMwNGFjMjcwOjAyMjRhMzY2LTcwMjMtNDQ3Yi1iOTJjLTJkOTJjNGIzNzU5Zg=="
        
        auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        
        rq_uid = str(uuid.uuid4())
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rq_uid,
            'Authorization': f'Basic {authorization_key}'
        }
        
        data = {
            'scope': 'GIGACHAT_API_PERS'
        }
        
        try:
            session = requests.Session()
            session.verify = False
            
            response = session.post(auth_url, headers=headers, data=data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                raise Exception(f"Ошибка аутентификации: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Exception: {str(e)}")
            raise Exception(f"Ошибка аутентификации: {str(e)}")

class GigaChatView(BaseGigaChatView):
    
    def post(self, request):
        message = request.data.get('message')
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return Response({'error': 'Сообщение обязательно'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation, created = Conversation.objects.get_or_create(session_id=session_id)
        
        Message.objects.create(
            conversation=conversation,
            content=message,
            is_user=True
        )
        
        try:
            access_token = self.get_access_token()
            
            history_messages = []
            for msg in conversation.messages.all().order_by('timestamp'):
                role = "user" if msg.is_user else "assistant"
                history_messages.append({"role": role, "content": msg.content})
            
            if len(history_messages) > 10:
                history_messages = history_messages[-10:]
            
            history_messages.append({"role": "user", "content": message})
            
            api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            payload = {
                "model": "GigaChat",
                "messages": history_messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            session = requests.Session()
            session.verify = False
            
            response = session.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            assistant_message = response_data['choices'][0]['message']['content']
            
            Message.objects.create(
                conversation=conversation,
                content=assistant_message,
                is_user=False
            )
            
            return Response({
                'response': assistant_message,
                'session_id': session_id
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EnhancedGigaChatView(BaseGigaChatView):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.corporate_culture_data = self.load_corporate_culture_data()
    
    def load_corporate_culture_data(self):
        return TrainingData.objects.filter(question_type='corporate_culture')
    
    def enhance_with_corporate_culture(self, message, history_messages):
        message_lower = message.lower()
        culture_keywords = [
            'алабуга', 'корпоративная', 'культура', 'оэз', 
            'ценност', 'миссия', 'команда', 'правила', 'этика',
            'сотрудник', 'работа', 'процесс', 'управление'
        ]
        
        if any(keyword in message_lower for keyword in culture_keywords):
            culture_context = "Ты - экспертный помощник по корпоративной культуре ОЭЗ АЛАБУГА. Вот важная информация:\n"
            for data in self.corporate_culture_data:
                culture_context += f"В: {data.question}\nО: {data.answer}\n\n"
            
            system_message = {
                "role": "system", 
                "content": culture_context + "Отвечай на вопросы, используя эту информацию. Будь полезным и дружелюбным."
            }
            
            enhanced_messages = [system_message] + history_messages
            return enhanced_messages
        
        return history_messages
    
    def post(self, request):
        message = request.data.get('message')
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return Response({'error': 'Сообщение обязательно'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation, created = Conversation.objects.get_or_create(session_id=session_id)
        
        Message.objects.create(
            conversation=conversation,
            content=message,
            is_user=True
        )
        
        try:
            access_token = self.get_access_token()
            
            history_messages = []
            for msg in conversation.messages.all().order_by('timestamp'):
                role = "user" if msg.is_user else "assistant"
                history_messages.append({"role": role, "content": msg.content})
            
            enhanced_messages = self.enhance_with_corporate_culture(message, history_messages)
            
            if len(enhanced_messages) > 12:
                enhanced_messages = [enhanced_messages[0]] + enhanced_messages[-11:]
            
            api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            payload = {
                "model": "GigaChat",
                "messages": enhanced_messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            session = requests.Session()
            session.verify = False
            
            response = session.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            assistant_message = response_data['choices'][0]['message']['content']
            
            Message.objects.create(
                conversation=conversation,
                content=assistant_message,
                is_user=False
            )
            
            return Response({
                'response': assistant_message,
                'session_id': session_id
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConversationView(APIView):
    def get(self, request, session_id):
        try:
            conversation = Conversation.objects.get(session_id=session_id)
            serializer = ConversationSerializer(conversation)
            return Response(serializer.data)
        except Conversation.DoesNotExist:
            return Response({'error': 'Беседа не найдена'}, status=status.HTTP_404_NOT_FOUND)

class MessageAllView(APIView):
    def get(self, request):
        messages = Message.objects.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def delete(self, request):
        Message.objects.all().delete()
        return Response({'message': "Все сообщения удалены"}, status=204)

class TrainingDataView(APIView):
    
    def get(self, request):
        training_data = TrainingData.objects.all()
        serializer = TrainingDataSerializer(training_data, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TrainingDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            training_data = TrainingData.objects.get(pk=pk)
            training_data.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TrainingData.DoesNotExist:
            return Response(
                {'error': 'Данные не найдены'}, 
                status=status.HTTP_404_NOT_FOUND
            )