from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.GigaChatView.as_view(), name='chat'),
    path('enhanced-chat/', views.EnhancedGigaChatView.as_view(), name='enhanced_chat'),
    path('conversation/<str:session_id>/', views.ConversationView.as_view(), name='conversation'),
    path('all/messages/', views.MessageAllView.as_view(), name='message'),
    path('training-data/', views.TrainingDataView.as_view(), name='training_data'),
    path('training-data/<int:pk>/', views.TrainingDataView.as_view(), name='training_data_detail'),
]