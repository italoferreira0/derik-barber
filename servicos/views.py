from django.shortcuts import render
from django.views.generic import ListView
from servicos.models import Servico, Planos

# Create your views here.
def ServicosView(request):
    servicos = Servico.objects.all()  # pega todos os serviços
    return render(request, "servicos.html", {"servicos": servicos})

class ServicosListView(ListView):
    model = Servico
    template_name = "servicos.html"
    context_object_name = "servicos"

def PlanosView(request):
    planos = Planos.objects.all()  # pega todos os serviços
    return render(request, "index.html", {"planos": planos})

class PlanosListView(ListView):
    model = Planos
    template_name = "index.html"
    context_object_name = "planos"
