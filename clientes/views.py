from django.shortcuts import render
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import CreateView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from clientes.models import Cliente

# Create your views here.
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
