from rest_framework import serializers
from .models import TextPrompt

class TextPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextPrompt
        fields = ['prompt', 'image_url']