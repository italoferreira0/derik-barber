from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from funcionarios.models import Funcionario, HorarioFuncionamento
from servicos.models import Planos, Servico
from agendamento.models import Agendamento
from clientes.models import Cliente
from django.db.models import Count, Sum
from datetime import date, datetime, time
from django.contrib import messages

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

class GerenciarHorariosView(SessionLoginRequiredMixin, TemplateView):
    template_name = 'gerenciar_horarios.html'
    
    def get(self, request, *args, **kwargs):
        horarios = HorarioFuncionamento.objects.all().order_by('dia_semana')
        
        # Cria uma lista de dicionários com os dados formatados para o template
        dias_com_horarios = []
        for dia, nome_dia in HorarioFuncionamento.DIAS_SEMANA:
            horario_existente = None
            for horario in horarios:
                if horario.dia_semana == dia:
                    horario_existente = horario
                    break
            
            dias_com_horarios.append({
                'dia': dia,
                'nome_dia': nome_dia,
                'horario': horario_existente,
                'ativo': horario_existente.ativo if horario_existente else False,
                'hora_inicio': horario_existente.hora_inicio.strftime('%H:%M') if horario_existente else '08:00',
                'hora_fim': horario_existente.hora_fim.strftime('%H:%M') if horario_existente else '18:00',
            })
        
        context = {
            'dias_com_horarios': dias_com_horarios,
            'dias_semana': HorarioFuncionamento.DIAS_SEMANA,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        try:
            # Processa cada dia da semana
            for dia, nome_dia in HorarioFuncionamento.DIAS_SEMANA:
                ativo = request.POST.get(f'dia_{dia}_ativo') == 'on'
                hora_inicio = request.POST.get(f'dia_{dia}_inicio')
                hora_fim = request.POST.get(f'dia_{dia}_fim')
                
                if ativo and hora_inicio and hora_fim:
                    # Cria ou atualiza o horário
                    horario, created = HorarioFuncionamento.objects.get_or_create(
                        dia_semana=dia,
                        defaults={
                            'hora_inicio': hora_inicio,
                            'hora_fim': hora_fim,
                            'ativo': True
                        }
                    )
                    
                    if not created:
                        horario.hora_inicio = hora_inicio
                        horario.hora_fim = hora_fim
                        horario.ativo = True
                        horario.save()
                else:
                    # Desativa o horário se não estiver marcado
                    try:
                        horario = HorarioFuncionamento.objects.get(dia_semana=dia)
                        horario.ativo = False
                        horario.save()
                    except HorarioFuncionamento.DoesNotExist:
                        pass
            
            messages.success(request, 'Horários de funcionamento atualizados com sucesso!')
            return redirect('gerenciar_horarios')
            
        except Exception as e:
            messages.error(request, f'Erro ao salvar horários: {str(e)}')
            return redirect('gerenciar_horarios')

def get_horarios_disponiveis(request):
    """API para retornar horários disponíveis em JSON"""
    data_agendamento = request.GET.get('data')
    if not data_agendamento:
        return JsonResponse({'error': 'Data não fornecida'}, status=400)
    
    try:
        data_obj = datetime.strptime(data_agendamento, '%Y-%m-%d').date()
        dia_semana = data_obj.weekday()
        
        # Busca horário de funcionamento para o dia
        try:
            horario_funcionamento = HorarioFuncionamento.objects.get(
                dia_semana=dia_semana, 
                ativo=True
            )
        except HorarioFuncionamento.DoesNotExist:
            return JsonResponse({'horarios': []})
        
        # Busca agendamentos existentes para o dia
        agendamentos = Agendamento.objects.filter(data=data_obj).values_list('hora', flat=True)
        horarios_ocupados = [ag.hour * 60 + ag.minute for ag in agendamentos]
        
        # Gera horários disponíveis
        horarios_disponiveis = []
        inicio = horario_funcionamento.hora_inicio
        fim = horario_funcionamento.hora_fim
        
        # Converte para minutos para facilitar cálculos
        inicio_minutos = inicio.hour * 60 + inicio.minute
        fim_minutos = fim.hour * 60 + fim.minute
        
        # Gera horários de 30 em 30 minutos
        for minutos in range(inicio_minutos, fim_minutos, 30):
            if minutos not in horarios_ocupados:
                hora = time(minutos // 60, minutos % 60)
                horarios_disponiveis.append({
                    'hora': hora.strftime('%H:%M'),
                    'display': hora.strftime('%H:%M')
                })
        
        return JsonResponse({'horarios': horarios_disponiveis})
        
    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class HistoricoAgendamentosView(SessionLoginRequiredMixin, TemplateView):
    template_name = 'historico_agendamentos.html'
    
    def get(self, request, *args, **kwargs):
        # Busca todos os agendamentos com informações do cliente e serviço
        agendamentos = Agendamento.objects.select_related('cliente', 'servico').order_by('-data', '-hora')
        
        context = {
            'agendamentos': agendamentos,
        }
        return render(request, self.template_name, context)


@csrf_protect
def get_servicos(request):
    """API para retornar lista de serviços em JSON"""
    # Verifica se o funcionário está logado
    if not request.session.get('funcionario_id'):
        return JsonResponse({'success': False, 'message': 'Acesso negado. Faça login primeiro.'}, status=401)
    
    servicos = Servico.objects.all().values('id', 'nome', 'preco')
    return JsonResponse({'servicos': list(servicos)})
