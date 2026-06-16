from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Une adresse email est requise.")
        email = self.normalize_email(email)
        if 'username' not in extra_fields:
            base = email.split('@')[0]
            username = base
            n = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base}{n}"
                n += 1
            extra_fields['username'] = username
        if 'role' in extra_fields and extra_fields['role']:
            extra_fields['role'] = extra_fields['role'].upper() # toujours en capitale
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('username', 'administrateur')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'PHOTOGRAPHE')

        return self.create_user(email, password, **extra_fields)
    

class Utilisateur(AbstractUser):

    class Role(models.TextChoices):
        PHOTOGRAPHE = "PHOTOGRAPHE", "Photographe"
        ASSISTANT = "ASSISTANT", "Assistant"
        CLIENT = "CLIENT", "Client"

    base_role = Role.CLIENT

    role = models.CharField(max_length = 50, choices=Role.choices)
    email = models.EmailField(unique=True, verbose_name="email")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UtilisateurManager()
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.role:
            self.role = self.base_role
        if self.role == Utilisateur.Role.ASSISTANT:
            self.is_staff = True
            self.is_superuser = False
        elif self.role == Utilisateur.Role.PHOTOGRAPHE:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email}"
    

class PhotographeManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        retour = super().get_queryset(*args, **kwargs)
        return retour.filter(role=Utilisateur.Role.PHOTOGRAPHE)

class Photographe(Utilisateur):
    base_role = Utilisateur.Role.PHOTOGRAPHE
    photographe = PhotographeManager()

    class Meta:
        proxy = True
        ordering = ('first_name',)

    
class AssistantManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        retour = super().get_queryset(*args, **kwargs)
        return retour.filter(role=Utilisateur.Role.ASSISTANT)

class Assistant(Utilisateur):
    base_role = Utilisateur.Role.ASSISTANT
    assistant = AssistantManager()

    class Meta:
        proxy = True
        ordering = ('first_name',)
        
class ClientManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        retour = super().get_queryset(*args, **kwargs)
        return retour.filter(role=Utilisateur.Role.CLIENT)
    
class Client(Utilisateur):
    base_role = Utilisateur.Role.CLIENT
    client = ClientManager()

    class Meta:
        proxy = True
        ordering = ('first_name',)

