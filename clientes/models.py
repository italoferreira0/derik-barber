from django.db import models

# Create your models here.
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True, blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    senha = models.CharField(max_length=255)

    def __str__(self):
        return self.nome