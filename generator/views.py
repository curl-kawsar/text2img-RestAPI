import logging
import os
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TextPrompt
from .serializers import TextPromptSerializer

logger = logging.getLogger(__name__)

class GenerateImageView(APIView):
    def post(self, request):
        try:
            prompt = request.data.get('prompt')
            if not prompt:
                return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Hugging Face API URL for Stable Diffusion 2.1
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API_KEY')}"}
            
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
            
            response = requests.post(API_URL, headers=headers, json=data)
            
            if response.status_code == 200:
                # Ensure the generated_images directory exists
                os.makedirs('generated_images', exist_ok=True)
                
                # Save the response image to a file
                image_path = f"generated_images/{prompt.replace(' ', '_')}.png"
                with open(image_path, "wb") as f:
                    f.write(response.content)
                
                # Assuming you have a way to serve the image files, generate the URL
                image_url = f"http://yourserver.com/{image_path}"
                
                text_prompt = TextPrompt.objects.create(prompt=prompt, image_url=image_url)
                serializer = TextPromptSerializer(text_prompt)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Failed to generate image: {response.text}")
                return Response({"error": "Failed to generate image"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("An error occurred while generating the image")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)