from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class IndexFuncionarioView(TemplateView):
    template_name = 'index_funcionario.html'
