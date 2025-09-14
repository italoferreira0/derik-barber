#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from agendamento.models import Agendamento
from servicos.models import Servico
from clientes.models import Cliente
from datetime import datetime, date, time

def testar_conflito():
    print("=== TESTE DE VALIDAÇÃO DE CONFLITO ===\n")
    
    # Buscar cliente e serviço
    cliente = Cliente.objects.filter(email='teste@teste.com').first()
    servico = Servico.objects.first()
    
    if not cliente or not servico:
        print("ERRO: Cliente ou serviço não encontrado")
        return
    
    print(f"Cliente: {cliente.nome}")
    print(f"Serviço: {servico.nome} (Duração: {servico.duracao})")
    print()
    
    # Mostrar agendamentos existentes
    agendamentos = Agendamento.objects.filter(data=date.today())
    print("Agendamentos existentes hoje:")
    for ag in agendamentos:
        inicio = ag.hora
        fim = datetime.combine(date.today(), ag.hora) + ag.servico.duracao
        print(f"- {inicio.strftime('%H:%M')} - {fim.time().strftime('%H:%M')} ({ag.servico.nome})")
    print()
    
    # Testar diferentes cenários
    cenarios_teste = [
        (time(15, 30), "15:30 - Deveria funcionar (antes do agendamento)"),
        (time(15, 59), "15:59 - Deveria funcionar (1 min antes)"),
        (time(16, 0), "16:00 - Deveria CONFLITAR (mesmo horário)"),
        (time(16, 15), "16:15 - Deveria CONFLITAR (durante o serviço)"),
        (time(16, 30), "16:30 - Deveria CONFLITAR (durante o serviço)"),
        (time(16, 44), "16:44 - Deveria CONFLITAR (último minuto)"),
        (time(16, 45), "16:45 - Deveria funcionar (quando termina)"),
        (time(17, 0), "17:00 - Deveria funcionar (depois do agendamento)"),
    ]
    
    for hora_teste, descricao in cenarios_teste:
        print(f"Testando {descricao}:")
        
        # Simular a validação que acontece na view
        hora_inicio = datetime.combine(date.today(), hora_teste)
        hora_fim = hora_inicio + servico.duracao
        
        conflito_detectado = False
        for agendamento in agendamentos:
            agendamento_inicio = datetime.combine(date.today(), agendamento.hora)
            agendamento_fim = agendamento_inicio + agendamento.servico.duracao
            
            # Verifica sobreposição
            if hora_inicio < agendamento_fim and hora_fim > agendamento_inicio:
                conflito_detectado = True
                print(f"  ❌ CONFLITO detectado com agendamento {agendamento.hora.strftime('%H:%M')} - {agendamento_fim.time().strftime('%H:%M')}")
                break
        
        if not conflito_detectado:
            print(f"  ✅ SEM conflito - horário disponível")
        print()

if __name__ == "__main__":
    testar_conflito()
