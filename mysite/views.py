from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.core.files.storage import FileSystemStorage

from django.http import HttpResponse

from . import util
 
def index(request):
    context = {}
    if request.method == 'POST':
        context = util.detectTrafficSign(request)
    context['title'] = 'Trang chủ'
    return render(request, 'index.html', context=context)

def guide(request):
    context = {}
    context['title'] = 'Hướng dẫn'
    return render(request, 'guide.html', context=context)

def contact(request):
    context = {}
    context['title'] = 'Liên hệ'
    return render(request, 'contact.html', context=context)
