from django.contrib import admin
from .models import Agendamento

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'servico', 'data', 'hora', 'criado_em']
    list_filter = ['data', 'servico', 'criado_em']
    search_fields = ['cliente__nome', 'cliente__email', 'servico__nome']
    date_hierarchy = 'data'
    ordering = ['data', 'hora']
