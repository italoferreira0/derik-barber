from django.urls import path
from funcionarios.views import *

urlpatterns = [
    path('', IndexFuncionarioView.as_view(), name='index_funcionario'),
    path('login/', LoginView.as_view(), name='login_funcionario'),
    path('cadastro/', CadastroFuncionarioView.as_view(), name='cadastro_funcionario'),
    path('logout/', LogoutView, name='logout_funcionario'),
]