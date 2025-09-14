from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView,CreateView, ListView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from servicos.models import Servico
from servicos.models import Planos
from clientes.models import Cliente
from agendamento.models import Agendamento
from django.contrib import messages
from django.db import models
from datetime import datetime, date, timedelta

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

@method_decorator(csrf_protect, name='dispatch')
class AgendaView(SessionLoginRequiredMixin, TemplateView):
    template_name = 'agenda.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicos'] = Servico.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        # Pega os dados do formulário
        servico_id = request.POST.get('servico')
        data_str = request.POST.get('data')
        hora_str = request.POST.get('horario')
        observacoes = request.POST.get('observacoes', '')
        
        # Pega o cliente da sessão
        cliente_id = request.session.get('cliente_id')
        
        try:
            # Validações básicas
            if not servico_id or not data_str or not hora_str:
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                return render(request, self.template_name, self.get_context_data())
            
            # Converte data e hora
            data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
            hora_agendamento = datetime.strptime(hora_str, '%H:%M').time()
            
            # Valida se a data não é no passado
            if data_agendamento < date.today():
                messages.error(request, 'Não é possível agendar para datas passadas.')
                return render(request, self.template_name, self.get_context_data())
            
            # Pega o serviço para obter a duração
            try:
                servico = Servico.objects.get(id=servico_id)
            except Servico.DoesNotExist:
                messages.error(request, 'Serviço não encontrado.')
                return render(request, self.template_name, self.get_context_data())
            
            # Calcula o horário de fim do serviço
            hora_inicio = datetime.combine(data_agendamento, hora_agendamento)
            hora_fim = hora_inicio + servico.duracao
            
            # Valida se não há conflito de horário considerando a duração
            # Pega todos os agendamentos do dia
            agendamentos_dia = Agendamento.objects.filter(data=data_agendamento).select_related('servico')
            
            # Verifica conflitos com cada agendamento existente
            for agendamento in agendamentos_dia:
                agendamento_inicio = datetime.combine(data_agendamento, agendamento.hora)
                agendamento_fim = agendamento_inicio + agendamento.servico.duracao
                
                # Verifica se há sobreposição de horários
                # Dois intervalos se sobrepõem se:
                # - O início de um está antes do fim do outro E
                # - O fim de um está depois do início do outro
                if hora_inicio < agendamento_fim and hora_fim > agendamento_inicio:
                    messages.error(request, 
                        f'Este horário conflita com um agendamento existente:\n'
                        f'• Horário ocupado: {agendamento.hora.strftime("%H:%M")} - {agendamento_fim.time().strftime("%H:%M")}\n'
                        f'• Seu horário: {hora_agendamento.strftime("%H:%M")} - {hora_fim.time().strftime("%H:%M")}\n'
                        f'Escolha outro horário.')
                    return render(request, self.template_name, self.get_context_data())
            
            # Cria o agendamento
            Agendamento.objects.create(
                cliente_id=cliente_id,
                servico_id=servico_id,
                data=data_agendamento,
                hora=hora_agendamento,
                observacoes=observacoes
            )
            
            messages.success(request, 'Agendamento realizado com sucesso!')
            return redirect('agenda')
            
        except ValueError:
            messages.error(request, 'Data ou horário inválidos.')
            return render(request, self.template_name, self.get_context_data())
        except Exception as e:
            messages.error(request, f'Erro ao processar agendamento: {str(e)}')
            return render(request, self.template_name, self.get_context_data())

from django.http import JsonResponse

def horarios_disponiveis(request):
    """View para retornar horários disponíveis em uma data específica"""
    if request.method == 'GET':
        data_str = request.GET.get('data')
        servico_id = request.GET.get('servico_id')
        
        if not data_str or not servico_id:
            return JsonResponse({'error': 'Data e serviço são obrigatórios'}, status=400)
        
        try:
            data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
            servico = Servico.objects.get(id=servico_id)
            
            # Horários ocupados no dia
            agendamentos_dia = Agendamento.objects.filter(data=data_agendamento).select_related('servico')
            
            # Lista de horários ocupados com suas durações
            horarios_ocupados = []
            for agendamento in agendamentos_dia:
                inicio = datetime.combine(data_agendamento, agendamento.hora)
                fim = inicio + agendamento.servico.duracao
                horarios_ocupados.append({
                    'inicio': agendamento.hora.strftime('%H:%M'),
                    'fim': fim.time().strftime('%H:%M'),
                    'duracao': str(agendamento.servico.duracao),
                    'servico': agendamento.servico.nome
                })
            
            return JsonResponse({
                'horarios_ocupados': horarios_ocupados,
                'duracao_servico': str(servico.duracao)
            })
            
        except (ValueError, Servico.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

class ContatoView(TemplateView):
    template_name = 'contato.html'