from django.urls import path
from funcionarios.views import *

urlpatterns = [
    path('', IndexFuncionarioView.as_view(), name='index_funcionario')
]