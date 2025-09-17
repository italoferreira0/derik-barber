from django.contrib import admin
from funcionarios.models import Funcionario, HorarioFuncionamento

# Register your models here.
@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'status', 'data_cadastro']
    list_filter = ['status', 'data_cadastro']
    search_fields = ['nome', 'email', 'telefone']
    readonly_fields = ['data_cadastro']

@admin.register(HorarioFuncionamento)
class HorarioFuncionamentoAdmin(admin.ModelAdmin):
    list_display = ['get_dia_semana_display', 'hora_inicio', 'hora_fim', 'ativo', 'data_criacao']
    list_filter = ['ativo', 'dia_semana']
    ordering = ['dia_semana']
    readonly_fields = ['data_criacao']