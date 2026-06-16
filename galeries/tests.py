import io
import shutil
import tempfile

from PIL import Image as PILImage

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Galerie, Collection, Tag, Photo, PhotoStorage


def _image_jpeg_valide(nom='test.jpg'):
    buffer = io.BytesIO()
    PILImage.new('RGB', (10, 10), color='red').save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(nom, buffer.read(), content_type='image/jpeg')


class GalerieSlugTests(TestCase):

    def test_slug_genere_a_la_creation(self):
        galerie = Galerie.objects.create(nom="Mariage de Julie")
        self.assertEqual(galerie.slug, "mariage-de-julie")

    def test_slug_non_regenere_si_le_nom_change(self):
        galerie = Galerie.objects.create(nom="Vacances")
        slug_initial = galerie.slug
        galerie.nom = "Vacances 2026"
        galerie.save()
        self.assertEqual(galerie.slug, slug_initial)

    def test_slug_unique_en_cas_de_collision(self):
        Galerie.objects.create(nom="Été")
        galerie2 = Galerie.objects.create(nom="Été")
        self.assertEqual(galerie2.slug, "ete-2")


class CollectionSlugTests(TestCase):

    def setUp(self):
        self.galerie = Galerie.objects.create(nom="Mariage")

    def test_slug_genere_a_la_creation(self):
        collection = Collection.objects.create(nom="Cérémonie", galerie=self.galerie)
        self.assertEqual(collection.slug, "ceremonie")

    def test_slug_unique_dans_la_meme_galerie(self):
        Collection.objects.create(nom="Photos", galerie=self.galerie)
        collection2 = Collection.objects.create(nom="Photos", galerie=self.galerie)
        self.assertEqual(collection2.slug, "photos-2")

    def test_meme_slug_autorise_dans_des_galeries_differentes(self):
        autre_galerie = Galerie.objects.create(nom="Anniversaire")
        Collection.objects.create(nom="Photos", galerie=self.galerie)
        collection_autre = Collection.objects.create(nom="Photos", galerie=autre_galerie)
        self.assertEqual(collection_autre.slug, "photos")


class TagSlugTests(TestCase):

    def test_slug_genere_a_la_creation(self):
        tag = Tag.objects.create(nom="Portrait")
        self.assertEqual(tag.slug, "portrait")

    def test_nom_unique(self):
        Tag.objects.create(nom="Nature")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tag.objects.create(nom="Nature")


class ComptagePhotosTests(TestCase):

    def setUp(self):
        self.galerie = Galerie.objects.create(nom="Studio")
        self.collection = Collection.objects.create(nom="Portraits", galerie=self.galerie)

    def _creer_photo(self):
        photo = Photo(image=_image_jpeg_valide())
        photo.save()
        self.addCleanup(photo.delete)
        return photo

    def test_nombre_collections(self):
        Collection.objects.create(nom="Studio annexe", galerie=self.galerie)
        self.assertEqual(self.galerie.nombre_collections(), 2)

    def test_nombre_photos_par_collection(self):
        photo = self._creer_photo()
        self.collection.photos.add(photo)
        self.assertEqual(self.collection.nombre_photos(), 1)

    def test_nombre_total_photos_additionne_direct_et_collection(self):
        photo_directe = self._creer_photo()
        photo_collection = self._creer_photo()
        self.galerie.photos.add(photo_directe)
        self.collection.photos.add(photo_collection)
        self.assertEqual(self.galerie.nombre_total_photos(), 2)

    def test_nombre_total_photos_sans_doublon(self):
        photo = self._creer_photo()
        self.galerie.photos.add(photo)
        self.collection.photos.add(photo)
        self.assertEqual(self.galerie.nombre_total_photos(), 1)


class PhotoStorageTests(TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.storage = PhotoStorage(location=self.tmp_dir)

    def test_nom_inchange_sans_collision(self):
        nom = self.storage.save('unique.jpg', _image_jpeg_valide())
        self.assertEqual(nom, 'unique.jpg')

    def test_renomme_en_cas_de_collision(self):
        nom1 = self.storage.save('photo.jpg', _image_jpeg_valide())
        nom2 = self.storage.save('photo.jpg', _image_jpeg_valide())
        nom3 = self.storage.save('photo.jpg', _image_jpeg_valide())
        self.assertEqual(nom1, 'photo.jpg')
        self.assertEqual(nom2, 'photo_001.jpg')
        self.assertEqual(nom3, 'photo_002.jpg')
