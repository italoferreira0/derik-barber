from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from servicos.models import Planos

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

class ContatoView(TemplateView):
    template_name = 'contato.html'