from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView,CreateView, ListView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from servicos.models import Servico


from clientes.models import Cliente

class IndexView(TemplateView):
    template_name = 'index.html'

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
                return redirect("index")
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

class AgendaView(TemplateView):
    template_name = 'agenda.html'

class ContatoView(TemplateView):
    template_name = 'contato.html'