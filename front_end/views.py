from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView,CreateView, ListView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from servicos.models import Servico
from servicos.models import Planos


from clientes.models import Cliente

# Mixin customizado para autenticação baseada em sessão
class SessionLoginRequiredMixin:
    """Mixin que verifica se o usuário está logado usando sessões customizadas"""
    login_url = reverse_lazy('login')
    redirect_field_name = 'next'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se existe cliente_id na sessão
        if not request.session.get('cliente_id'):
            return redirect(f"{self.login_url}?{self.redirect_field_name}={request.get_full_path()}")
        return super().dispatch(request, *args, **kwargs)

class IndexView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Planos.objects.all()
        return context

class LoginView(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        usuario = request.POST.get("usuario")  # email ou telefone
        senha = request.POST.get("senha")

        # Busca pelo email ou telefone
        cliente = Cliente.objects.filter(email=usuario).first() or Cliente.objects.filter(telefone=usuario).first()

        if cliente:
            if check_password(senha, cliente.senha):
                # Salva id e nome na sessão
                request.session["cliente_id"] = cliente.id
                request.session["cliente_nome"] = cliente.nome
                
                # Redireciona para a próxima página ou para index
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                return render(request, "login.html", {"erro": "Senha incorreta"})
        else:
            return render(request, "login.html", {"erro": "Usuário não encontrado"})
        
def LogoutView(request):
    request.session.flush()  # remove todas as variáveis de sessão
    return redirect("index")

@method_decorator(csrf_protect, name='dispatch')
class CadastroView(CreateView):
    def get(self, request):
        return render(request, "cadastro.html")

    def post(self, request):
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        telefone = request.POST.get("telefone")
        senha = request.POST.get("senha")

        # Criptografa a senha
        senha_criptografada = make_password(senha)

        # Cria o cliente
        Cliente.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            senha=senha_criptografada
        )

        return redirect("login")

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

class AgendaView(SessionLoginRequiredMixin, TemplateView):
    template_name = 'agenda.html'


class ContatoView(TemplateView):
    template_name = 'contato.html'