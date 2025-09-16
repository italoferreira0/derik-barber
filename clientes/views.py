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
        confirmar_senha = request.POST.get("confirmar_senha")

        # Validações
        erros = []
        
        if not nome or len(nome.strip()) < 2:
            erros.append("Nome deve ter pelo menos 2 caracteres")
        
        if not email or '@' not in email:
            erros.append("Email inválido")
        
        if not telefone or len(telefone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')) < 10:
            erros.append("Telefone inválido")
        
        if not senha or len(senha) < 6:
            erros.append("Senha deve ter pelo menos 6 caracteres")
        
        if senha != confirmar_senha:
            erros.append("Senhas não coincidem")
        
        # Verifica se email já existe
        if Cliente.objects.filter(email=email).exists():
            erros.append("Email já cadastrado")
        
        if erros:
            return render(request, "cadastro.html", {"erros": erros})

        try:
            # Criptografa a senha
            senha_criptografada = make_password(senha)

            # Cria o cliente
            Cliente.objects.create(
                nome=nome.strip(),
                email=email.strip().lower(),
                telefone=telefone.strip(),
                senha=senha_criptografada
            )

            return render(request, "cadastro.html", {
                "sucesso": "Cliente cadastrado com sucesso! Faça login para continuar."
            })
            
        except Exception as e:
            return render(request, "cadastro.html", {
                "erros": ["Erro interno. Tente novamente."]
            })
