from django.shortcuts import render
from .models import Post

def index(request):
    posts = Post.objects.all().order_by('-created_at')
    context = {
        'posts': posts,
    }
    return render(request, 'example_app/index.html', context)
