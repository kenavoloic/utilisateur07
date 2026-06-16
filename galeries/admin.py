from django import forms
from django.contrib import admin, messages
from django.forms.widgets import ClearableFileInput
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html

from .models import Photo


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={'accept': '.jpg,.jpeg'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return single_clean(data, initial)


class BatchUploadForm(forms.Form):
    images = MultipleFileField(label="Photos (JPG/JPEG)")


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):

    list_display    = ('vignette', 'nom_fichier', 'appareil', 'date_prise_de_vue', 'largeur', 'hauteur', 'taille')
    list_filter     = ('appareil', 'date_prise_de_vue')
    search_fields   = ('nom_fichier', 'titre', 'description', 'appareil', 'objectif')
    readonly_fields = (
        'vignette', 'nom_fichier', 'taille', 'largeur', 'hauteur',
        'appareil', 'objectif', 'ouverture', 'vitesse', 'iso',
        'date_prise_de_vue', 'latitude', 'longitude',
    )

    fieldsets = (
        ("Fichier", {
            "fields": ('vignette', 'image', 'nom_fichier', 'taille', 'largeur', 'hauteur', 'auteur'),
        }),
        ("Contenu", {
            "fields": ('titre', 'description'),
        }),
        ("Prise de vue", {
            "fields": ('date_prise_de_vue', 'appareil', 'objectif', 'ouverture', 'vitesse', 'iso'),
            "classes": ('collapse',),
        }),
        ("GPS", {
            "fields": ('latitude', 'longitude'),
            "classes": ('collapse',),
        }),
    )

    change_list_template = 'admin/galeries/photo/change_list.html'

    @admin.display(description='Vignette')
    def vignette(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;">', obj.image.url)
        return '-'

    def has_add_permission(self, request):
        return request.user.role in ('PHOTOGRAPHE', 'ASSISTANT')

    def has_change_permission(self, request, obj=None):
        return request.user.role in ('PHOTOGRAPHE', 'ASSISTANT')

    def has_delete_permission(self, request, obj=None):
        return request.user.role in ('PHOTOGRAPHE', 'ASSISTANT')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('batch-upload/', self.admin_site.admin_view(self.batch_upload_view), name='galeries_photo_batch_upload'),
        ]
        return custom_urls + urls

    def batch_upload_view(self, request):
        if not self.has_add_permission(request):
            messages.error(request, "Vous n'avez pas la permission d'uploader des photos.")
            return HttpResponseRedirect('../')

        if request.method == 'POST':
            form = BatchUploadForm(request.POST, request.FILES)
            if form.is_valid():
                fichiers = request.FILES.getlist('images')
                nb_succes = 0
                for fichier in fichiers:
                    photo = Photo(auteur=request.user)
                    photo.image.save(fichier.name, fichier, save=True)
                    nb_succes += 1
                messages.success(request, f"{nb_succes} photo(s) uploadée(s) avec succès.")
                return HttpResponseRedirect('../')
        else:
            form = BatchUploadForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Upload en lot',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/galeries/photo/batch_upload.html', context)
