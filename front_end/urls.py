from django.contrib import admin
from django.urls import path, include
from front_end.views import *


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path("logout/", LogoutView, name="logout"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("servicos/", ServicosView, name="servicos"),
    path("agenda/", AgendaView.as_view(), name="agenda"),
    path("horarios-disponiveis/", horarios_disponiveis, name="horarios_disponiveis"),
    path("contato/", ContatoView.as_view(), name="contato"),

]
