from django.db import models

# Create your models here.
class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    duracao = models.DurationField(help_text="Duração do serviço (hh:mm:ss)")
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    imagem = models.ImageField(upload_to='servicos/', blank=True, null=True)

    def __str__(self):
        return self.nome
    
class Planos(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    imagem = models.ImageField(upload_to='planos/', blank=True, null=True)

    def __str__(self):
        return self.nome