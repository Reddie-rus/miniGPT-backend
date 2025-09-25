from django.db import models

class Conversation(models.Model):
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class TrainingData(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('corporate_culture', 'Корпоративная культура'),
        ('general', 'Общие вопросы'),
    ]
    
    question = models.TextField(verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    question_type = models.CharField(
        max_length=20, 
        choices=QUESTION_TYPE_CHOICES,
        default='general',
        verbose_name="Тип вопроса"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.question_type}: {self.question[:50]}..."