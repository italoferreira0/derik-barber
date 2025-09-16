from django.urls import path
from main.views import *
from clientes.views import LoginView, LogoutView, CadastroView
from agendamento.views import MyAgendamentos, AgendaView, horarios_disponiveis, deletar_agendamento
from servicos.views import ServicosView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path("logout/", LogoutView, name="logout"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("servicos/", ServicosView, name="servicos"),
    path("agenda/", AgendaView.as_view(), name="agenda"),
    path("horarios-disponiveis/", horarios_disponiveis, name="horarios_disponiveis"),
    path("contato/", ContatoView.as_view(), name="contato"),
    path("my-agendamento/", MyAgendamentos.as_view(), name="my-agendamento"),
    path("deletar-agendamento/<int:agendamento_id>/", deletar_agendamento, name="deletar-agendamento"),
]
