from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur, Photographe, Assistant, Client

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):

    list_display = ('username','email','role','is_staff','last_login',)
    readonly_fields = ('created_at','updated_at',)
    list_filter = ('role', 'is_staff', 'is_active',)

    ordering = ('email','username','last_login','date_joined',)

    search_fields = ('email','username', 'first_name', 'last_name',)
    
    fieldsets = (
        ("Identité", {
            "fields": ('username','email','first_name', 'last_name',)
        }),
        ("Rôle", {
            "fields": ('role', 'is_staff', 'is_superuser','is_active',)
        }),
        ("Dates", {
            "fields": ('created_at', 'updated_at', 'last_login', 'date_joined',),
            "classes": ('collapse',),
        }),
    )

    add_fieldsets = (
        ("Identité", {
            "fields": ('email','username', 'first_name', 'last_name','password1','password2',),
            "classes": ('wide',)
            }),
    )

    
@admin.register(Photographe)
class PhotographeAdmin(UtilisateurAdmin):
    pass

@admin.register(Assistant)
class AssistantAdmin(UtilisateurAdmin):
    pass

@admin.register(Client)
class ClientAdmin(UtilisateurAdmin):
    pass
