import logging
import os
import requests
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TextPrompt
from .serializers import TextPromptSerializer
from django.conf import settings

logger = logging.getLogger(__name__)

class GenerateImageView(APIView):
    def post(self, request):
        try:
            prompt = request.data.get('prompt')
            if not prompt:
                return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Hugging Face API URL for Stable Diffusion 2.1
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
            headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}
            
            # Input text prompt with additional parameters for higher quality
            data = {
                "inputs": prompt,
                "options": {
                    "steps": 100,  # Increase the number of inference steps for finer details
                    "cfg_scale": 10.0,  # Adjust the classifier-free guidance scale for sharper images
                    "width": 1024,  # Increase resolution width
                    "height": 1024  # Increase resolution height
                }
            }
            
            # Retry logic for handling rate limiting
            max_retries = 1
            for attempt in range(max_retries):
                response = requests.post(API_URL, headers=headers, json=data)
                if response.status_code == 200:
                    # Ensure the media directory exists
                    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                    
                    # Save the response image to a file
                    image_filename = f"{prompt.replace(' ', '_')}.png"
                    image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    
                    # Generate the URL for the saved image
                    image_url = f"{settings.MEDIA_URL}{image_filename}"
                    
                    text_prompt = TextPrompt.objects.create(prompt=prompt, image_url=image_url)
                    serializer = TextPromptSerializer(text_prompt)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                elif response.status_code == 429:
                    logger.warning(f"Rate limited: {response.text}. Retrying in 5 seconds...")
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    logger.error(f"Failed to generate image: {response.text}")
                    return Response({"error": "Failed to generate image"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # If all retries fail
            return Response({"error": "Failed to generate image after multiple attempts"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("An error occurred while generating the image")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
