from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Material, Subject


class MaterialUploadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("upload-owner")
        cls.other = get_user_model().objects.create_user("upload-other")
        cls.subject = Subject.objects.create(owner=cls.owner, name="Python")

    def setUp(self):
        self.client.force_login(self.owner)

    def upload(self, name="Bài ôn tập.pdf", content=b"%PDF-1.4\nStudy notes"):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    def create_material(self):
        response = self.client.post(reverse("studies:material_create"), {
            "title": "Notes", "subject": self.subject.pk, "attachment": self.upload(), "owner": self.other.pk,
        })
        self.assertEqual(response.status_code, 302)
        return Material.objects.get(title="Notes")

    def test_uploaded_file_is_stored_in_database_and_only_owner_can_download(self):
        material = self.create_material()
        self.assertEqual(material.owner, self.owner)
        self.assertEqual(material.url, "")
        self.assertEqual(bytes(material.file_data), b"%PDF-1.4\nStudy notes")
        path = reverse("studies:material_download", args=[material.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), bytes(material.file_data))
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        self.assertIn("filename*=utf-8", response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(Client().get(path).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_invalid_uploads_and_empty_material_do_not_save_any_records(self):
        for file, field in ((None, "url"), (self.upload("bad.html", b"<script>bad</script>"), "attachment"),
                            (self.upload(content=b""), "attachment"),
                            (self.upload(content=b"x" * (10 * 1024 * 1024 + 1)), "attachment")):
            with self.subTest(field=field, file=file):
                data = {"title": "Invalid"}
                if file is not None:
                    data["attachment"] = file
                response = self.client.post(reverse("studies:material_create"), data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertFalse(Material.objects.exists())

    def test_edit_preserves_file_replaces_it_and_requires_link_before_removal(self):
        material = self.create_material()
        path = reverse("studies:material_update", args=[material.pk])
        self.assertEqual(self.client.post(path, {"title": "Renamed"}).status_code, 302)
        material.refresh_from_db()
        self.assertEqual(bytes(material.file_data), b"%PDF-1.4\nStudy notes")
        self.assertEqual(self.client.post(path, {"title": "Renamed", "attachment": self.upload("new.txt", b"New notes")}).status_code, 302)
        material.refresh_from_db()
        self.assertEqual((material.file_name, bytes(material.file_data)), ("new.txt", b"New notes"))
        response = self.client.post(path, {"title": "Renamed", "remove_attachment": "on"})
        self.assertEqual(response.status_code, 200)
        material.refresh_from_db()
        self.assertEqual(bytes(material.file_data), b"New notes")
        self.assertEqual(self.client.post(path, {"title": "Renamed", "url": "https://example.com/notes", "remove_attachment": "on"}).status_code, 302)
        material.refresh_from_db()
        self.assertIsNone(material.file_data)
        self.assertEqual(material.file_name, "")
        self.assertEqual(self.client.get(reverse("studies:material_download", args=[material.pk])).status_code, 404)

    def test_sidebar_upload_and_multipart_forms_show_protected_download_links(self):
        sidebar = reverse("planner:week") + "?panel=materials"
        for path in (reverse("studies:material_create"), sidebar + "&action=new"):
            self.assertContains(self.client.get(path), 'enctype="multipart/form-data"')
        response = self.client.post(sidebar, {"operation": "save", "title": "Sidebar upload", "attachment": self.upload()})
        self.assertEqual(response.status_code, 302)
        material = Material.objects.get(title="Sidebar upload")
        link = reverse("studies:material_download", args=[material.pk])
        for path in (sidebar, reverse("studies:material_list")):
            response = self.client.get(path)
            self.assertContains(response, link)
            objects = response.context["sidebar_page"] if path == sidebar else response.context["object_list"]
            self.assertIn("file_data", list(objects)[0].get_deferred_fields())
        self.client.post(sidebar, {"operation": "delete", "object_id": material.pk})
        self.assertFalse(Material.objects.filter(pk=material.pk).exists())
        self.assertEqual(self.client.get(link).status_code, 404)

    def test_upload_rejects_foreign_relations_and_requires_csrf(self):
        subject = Subject.objects.create(owner=self.other, name="Other subject")
        response = self.client.post(reverse("studies:material_create"), {
            "title": "Forged", "subject": subject.pk, "attachment": self.upload(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("subject", response.context["form"].errors)
        self.assertFalse(Material.objects.exists())
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.owner)
        self.assertEqual(strict.post(reverse("studies:material_create"), {
            "title": "No CSRF", "attachment": self.upload(),
        }).status_code, 403)
