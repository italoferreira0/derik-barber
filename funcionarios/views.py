from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from funcionarios.models import Funcionario
from servicos.models import Planos, Servico
from agendamento.models import Agendamento
from clientes.models import Cliente
from django.db.models import Count, Sum
from datetime import date, datetime

# Mixin customizado para autenticação baseada em sessão
class SessionLoginRequiredMixin:
    """Mixin que verifica se o usuário está logado usando sessões customizadas"""
    login_url = reverse_lazy('login_funcionario')
    redirect_field_name = 'next'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se existe funcionario_id na sessão
        if not request.session.get('funcionario_id'):
            return redirect(f"{self.login_url}?{self.redirect_field_name}={request.get_full_path()}")
        return super().dispatch(request, *args, **kwargs)

class IndexFuncionarioView(SessionLoginRequiredMixin, TemplateView):
    template_name = 'index_funcionario.html'
    
    def get(self, request, *args, **kwargs):
        # Adiciona informações do funcionário no contexto
        funcionario_id = request.session.get('funcionario_id')
        funcionario_nome = request.session.get('funcionario_nome')
        
        # Busca estatísticas gerais
        total_clientes = Cliente.objects.count()
        total_agendamentos = Agendamento.objects.count()
        total_servicos = Servico.objects.count()
        
        # Agendamentos do dia atual
        hoje = date.today()
        agendamentos_hoje = Agendamento.objects.filter(data=hoje).select_related('cliente', 'servico').order_by('hora')
        
        # Próximos agendamentos (próximos 7 dias)
        proximos_agendamentos = Agendamento.objects.filter(
            data__gte=hoje
        ).select_related('cliente', 'servico').order_by('data', 'hora')[:10]
        
        # Receita total do dia
        receita_hoje = Agendamento.objects.filter(data=hoje).aggregate(
            total=Sum('servico__preco')
        )['total'] or 0
        
        # Serviços mais populares
        servicos_populares = Servico.objects.annotate(
            total_agendamentos=Count('agendamento')
        ).order_by('-total_agendamentos')[:5]
        
        context = {
            'funcionario_nome': funcionario_nome,
            'funcionario_id': funcionario_id,
            'total_clientes': total_clientes,
            'total_agendamentos': total_agendamentos,
            'total_servicos': total_servicos,
            'agendamentos_hoje': agendamentos_hoje,
            'proximos_agendamentos': proximos_agendamentos,
            'receita_hoje': receita_hoje,
            'servicos_populares': servicos_populares,
        }
        return render(request, self.template_name, context)

class LoginView(View):
    def get(self, request):
        # Se já estiver logado, redireciona para a área do funcionário
        if request.session.get('funcionario_id'):
            return redirect('index_funcionario')
        return render(request, "login_funcionario.html")

    def post(self, request):
        # Se já estiver logado, redireciona para a área do funcionário
        if request.session.get('funcionario_id'):
            return redirect('index_funcionario')
            
        usuario = request.POST.get("usuario")  # email ou telefone
        senha = request.POST.get("senha")

        # Busca pelo email ou telefone
        funcionario = Funcionario.objects.filter(email=usuario).first() or Funcionario.objects.filter(telefone=usuario).first()

        if funcionario:
            if not funcionario.status:
                return render(request, "login_funcionario.html", {"erro": "Sua conta está inativa. Entre em contato com o administrador."})
            
            if check_password(senha, funcionario.senha):
                # Salva id e nome na sessão
                request.session["funcionario_id"] = funcionario.id
                request.session["funcionario_nome"] = funcionario.nome
                
                # Redireciona para a próxima página ou para index
                next_url = request.GET.get('next', 'index_funcionario')
                return redirect(next_url)
            else:
                return render(request, "login_funcionario.html", {"erro": "Senha incorreta"})
        else:
            return render(request, "login_funcionario.html", {"erro": "Usuário não encontrado"})
        
def LogoutView(request):
    request.session.flush()  # remove todas as variáveis de sessão
    return redirect("index")

@method_decorator(csrf_protect, name='dispatch')
class CadastroFuncionarioView(View):
    def get(self, request):
        # Se já estiver logado, redireciona para a área do funcionário
        if request.session.get('funcionario_id'):
            return redirect('index_funcionario')
        return render(request, "cadastro_funcionario.html")

    def post(self, request):
        # Se já estiver logado, redireciona para a área do funcionário
        if request.session.get('funcionario_id'):
            return redirect('index_funcionario')
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
        if Funcionario.objects.filter(email=email).exists():
            erros.append("Email já cadastrado")
        
        if erros:
            return render(request, "cadastro_funcionario.html", {"erros": erros})

        try:
            # Criptografa a senha
            senha_criptografada = make_password(senha)

            # Cria o funcionário
            Funcionario.objects.create(
                nome=nome.strip(),
                email=email.strip().lower(),
                telefone=telefone.strip(),
                senha=senha_criptografada
            )

            return render(request, "cadastro_funcionario.html", {
                "sucesso": "Funcionário cadastrado com sucesso! Faça login para continuar."
            })
            
        except Exception as e:
            return render(request, "cadastro_funcionario.html", {
                "erros": ["Erro interno. Tente novamente."]
            })
