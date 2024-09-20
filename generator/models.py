from django.db import models

class TextPrompt(models.Model):
    prompt = models.CharField(max_length=255)
    image_url = models.URLField()