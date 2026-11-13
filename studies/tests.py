from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Material, Subject, Task

User = get_user_model()


class StudyFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="study_owner")
        cls.other = User.objects.create_user(username="study_other")
        cls.subject = Subject.objects.create(owner=cls.owner, name="Python", semester="HK1")
        cls.other_subject = Subject.objects.create(owner=cls.other, name="Private subject B")
        cls.task = Task.objects.create(
            owner=cls.owner, subject=cls.subject, title="Python report",
            deadline=timezone.now() + timedelta(days=2), priority=Task.Priority.HIGH,
            estimated_minutes=180, remaining_minutes=180,
        )
        cls.late_task = Task.objects.create(
            owner=cls.owner, title="Late exercise", deadline=timezone.now() - timedelta(hours=1),
            estimated_minutes=30, remaining_minutes=30,
        )
        cls.done_task = Task.objects.create(
            owner=cls.owner, title="Completed exercise", deadline=timezone.now() - timedelta(days=1),
            estimated_minutes=60, remaining_minutes=0, status=Task.Status.DONE,
        )
        cls.other_task = Task.objects.create(
            owner=cls.other, subject=cls.other_subject, title="Private task B",
            deadline=timezone.now() + timedelta(days=1), estimated_minutes=90, remaining_minutes=90,
        )
        cls.material = Material.objects.create(
            owner=cls.owner, subject=cls.subject, task=cls.task,
            title="Python docs", url="https://docs.python.org/3/",
        )
        cls.other_material = Material.objects.create(
            owner=cls.other, subject=cls.other_subject, task=cls.other_task,
            title="Private material B", url="https://example.com/private",
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def task_data(self, **overrides):
        data = {
            "title": "New assignment", "subject": self.subject.pk,
            "description": "Prepare report",
            "deadline": timezone.localtime(timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
            "priority": Task.Priority.HIGH, "estimated_minutes": 120,
            "can_split": "on", "status": Task.Status.TODO,
        }
        data.update(overrides)
        return data

    def material_data(self, **overrides):
        data = {
            "title": "Course notes", "url": "https://example.com/notes",
            "subject": self.subject.pk, "task": self.task.pk, "description": "Reference",
        }
        data.update(overrides)
        return data

    def test_all_study_pages_require_login(self):
        client = Client()
        for prefix, obj in (("subject", self.subject), ("task", self.task), ("material", self.material)):
            for action in ("list", "create", "update", "delete"):
                with self.subTest(prefix=prefix, action=action):
                    args = [obj.pk] if action in ("update", "delete") else []
                    response = client.get(reverse(f"studies:{prefix}_{action}", args=args))
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_lists_and_relation_choices_only_show_owned_records(self):
        for prefix, model, hidden in (
            ("subject", Subject, self.other_subject.name),
            ("task", Task, self.other_task.title),
            ("material", Material, self.other_material.title),
        ):
            with self.subTest(prefix=prefix):
                response = self.client.get(reverse(f"studies:{prefix}_list"))
                self.assertEqual(response.status_code, 200)
                self.assertSetEqual(
                    set(response.context["object_list"].values_list("pk", flat=True)),
                    set(model.objects.filter(owner=self.owner).values_list("pk", flat=True)),
                )
                self.assertNotContains(response, hidden)
        for name in ("task_create", "material_create"):
            response = self.client.get(reverse(f"studies:{name}"))
            self.assertNotContains(response, self.other_subject.name)
            self.assertNotContains(response, self.other_task.title)

    def test_foreign_ids_cannot_be_read_edited_or_deleted(self):
        for prefix, obj in (("subject", self.other_subject), ("task", self.other_task), ("material", self.other_material)):
            for action in ("update", "delete"):
                path = reverse(f"studies:{prefix}_{action}", args=[obj.pk])
                for method in (self.client.get, self.client.post):
                    with self.subTest(path=path, method=method.__name__):
                        self.assertEqual(method(path, {}).status_code, 404)
            self.assertTrue(type(obj).objects.filter(pk=obj.pk, owner=self.other).exists())

    def test_subject_create_ignores_forged_owner(self):
        response = self.client.post(reverse("studies:subject_create"), {
            "name": "Databases", "semester": "HK2", "color": "#123abc", "owner": self.other.pk,
        })
        self.assertRedirects(response, reverse("studies:subject_list"))
        subject = Subject.objects.get(name="Databases")
        self.assertEqual(subject.owner, self.owner)
        self.assertEqual(subject.color, "#123abc")

    def test_subject_archive_search_and_restore_preserve_links(self):
        path = reverse("studies:subject_update", args=[self.subject.pk])
        data = {"name": "Python", "semester": "HK1", "color": "#176b58", "is_archived": "on"}
        self.assertRedirects(self.client.post(path, data), reverse("studies:subject_list"))
        response = self.client.get(reverse("studies:subject_list"))
        self.assertEqual(list(response.context["object_list"]), [])
        response = self.client.get(reverse("studies:subject_list"), {"state": "archived", "q": "Python"})
        self.assertEqual(list(response.context["object_list"]), [self.subject])
        self.task.refresh_from_db()
        self.material.refresh_from_db()
        self.assertEqual(self.task.subject_id, self.subject.pk)
        self.assertEqual(self.material.subject_id, self.subject.pk)
        data.pop("is_archived")
        self.client.post(path, data)
        self.subject.refresh_from_db()
        self.assertFalse(self.subject.is_archived)

    def test_subject_delete_needs_confirmation_and_keeps_tasks_and_materials(self):
        path = reverse("studies:subject_delete", args=[self.subject.pk])
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertTrue(Subject.objects.filter(pk=self.subject.pk).exists())
        self.assertRedirects(self.client.post(path), reverse("studies:subject_list"))
        self.task.refresh_from_db()
        self.material.refresh_from_db()
        self.assertIsNone(self.task.subject_id)
        self.assertIsNone(self.material.subject_id)
        self.assertEqual(self.material.task_id, self.task.pk)

    def test_subject_rejects_missing_name_and_invalid_color(self):
        for changes, field in (({"name": ""}, "name"), ({"color": "red"}, "color")):
            with self.subTest(changes=changes):
                data = {"name": "New subject", "color": "#176b58", **changes}
                response = self.client.post(reverse("studies:subject_create"), data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(Subject.objects.count(), 2)

    def test_task_create_sets_remaining_minutes_and_converts_local_deadline(self):
        data = self.task_data(owner=self.other.pk, remaining_minutes=1)
        self.assertRedirects(self.client.post(reverse("studies:task_create"), data), reverse("studies:task_list"))
        task = Task.objects.get(title=data["title"])
        self.assertEqual(task.owner, self.owner)
        self.assertEqual(task.remaining_minutes, 120)
        self.assertEqual(timezone.localtime(task.deadline).strftime("%Y-%m-%dT%H:%M"), data["deadline"])
        response = self.client.get(reverse("studies:task_update", args=[task.pk]))
        self.assertContains(response, f'value="{data["deadline"]}"')

    def test_task_can_be_created_completed(self):
        response = self.client.post(reverse("studies:task_create"), self.task_data(status=Task.Status.DONE))
        self.assertRedirects(response, reverse("studies:task_list"))
        self.assertEqual(Task.objects.get(title="New assignment").remaining_minutes, 0)

    def test_task_completion_and_reopening_update_remaining_time(self):
        path = reverse("studies:task_update", args=[self.task.pk])
        response = self.client.post(path, self.task_data(status=Task.Status.DONE, remaining_minutes=100))
        self.assertRedirects(response, reverse("studies:task_list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.remaining_minutes, 0)
        response = self.client.post(path, self.task_data(status=Task.Status.IN_PROGRESS, remaining_minutes=200))
        self.assertRedirects(response, reverse("studies:task_list"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.remaining_minutes, 200)
        self.assertEqual(self.task.status, Task.Status.IN_PROGRESS)

    def test_task_rejects_invalid_estimates_deadlines_and_choices(self):
        cases = [
            ({"estimated_minutes": 0}, "estimated_minutes"),
            ({"estimated_minutes": -1}, "estimated_minutes"),
            ({"estimated_minutes": ""}, "estimated_minutes"),
            ({"deadline": "not-a-date"}, "deadline"),
            ({"priority": 99}, "priority"),
            ({"status": "unknown"}, "status"),
        ]
        for changes, field in cases:
            with self.subTest(changes=changes):
                response = self.client.post(reverse("studies:task_create"), self.task_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(Task.objects.count(), 4)
        for remaining in (-1, 0):
            response = self.client.post(
                reverse("studies:task_update", args=[self.task.pk]), self.task_data(remaining_minutes=remaining)
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("remaining_minutes", response.context["form"].errors)

    def test_overdue_filter_excludes_completed_tasks_and_accepts_past_deadlines(self):
        past = timezone.localtime(timezone.now() - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
        self.assertRedirects(
            self.client.post(reverse("studies:task_create"), self.task_data(deadline=past)),
            reverse("studies:task_list"),
        )
        task = Task.objects.get(title="New assignment")
        self.assertTrue(task.is_overdue)
        response = self.client.get(reverse("studies:task_list"), {"status": "overdue"})
        self.assertSetEqual(set(response.context["object_list"]), {self.late_task, task})
        self.assertFalse(self.done_task.is_overdue)

    def test_task_search_and_filters_combine_and_reject_foreign_subject(self):
        path = reverse("studies:task_list")
        response = self.client.get(path, {
            "q": "Python", "subject": self.subject.pk, "status": "todo", "priority": 3,
        })
        self.assertEqual(list(response.context["object_list"]), [self.task])
        for data, field in (({"subject": self.other_subject.pk}, "subject"), ({"priority": "abc"}, "priority")):
            response = self.client.get(path, data)
            self.assertEqual(response.status_code, 200)
            self.assertIn(field, response.context["filter_form"].errors)
            self.assertEqual(list(response.context["object_list"]), [])

    def test_foreign_subject_and_task_cannot_be_linked_through_forms(self):
        response = self.client.post(reverse("studies:task_create"), self.task_data(subject=self.other_subject.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIn("subject", response.context["form"].errors)
        self.assertNotContains(response, self.other_subject.name)
        response = self.client.post(
            reverse("studies:material_create"),
            self.material_data(subject=self.other_subject.pk, task=self.other_task.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("subject", response.context["form"].errors)
        self.assertIn("task", response.context["form"].errors)
        self.assertEqual(Task.objects.count(), 4)
        self.assertEqual(Material.objects.count(), 2)

    def test_model_validation_also_checks_relation_ownership(self):
        task = Task(
            owner=self.owner, subject=self.other_subject, title="Invalid relation",
            deadline=timezone.now(), estimated_minutes=30, remaining_minutes=30,
        )
        with self.assertRaises(ValidationError) as error:
            task.full_clean()
        self.assertIn("subject", error.exception.message_dict)
        material = Material(owner=self.owner, subject=self.other_subject, task=self.other_task,
                            title="Invalid relation", url="https://example.com/")
        with self.assertRaises(ValidationError) as error:
            material.full_clean()
        self.assertSetEqual(set(error.exception.message_dict), {"subject", "task"})

    def test_material_create_update_and_delete_keep_related_learning_data(self):
        self.assertRedirects(
            self.client.post(reverse("studies:material_create"), self.material_data(owner=self.other.pk)),
            reverse("studies:material_list"),
        )
        material = Material.objects.get(title="Course notes")
        self.assertEqual(material.owner, self.owner)
        self.assertEqual(material.task_id, self.task.pk)
        self.assertRedirects(
            self.client.post(reverse("studies:material_update", args=[material.pk]), self.material_data(task="", url="https://example.com/updated")),
            reverse("studies:material_list"),
        )
        material.refresh_from_db()
        self.assertIsNone(material.task_id)
        self.assertEqual(material.url, "https://example.com/updated")
        path = reverse("studies:material_delete", args=[material.pk])
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertTrue(Material.objects.filter(pk=material.pk).exists())
        self.assertRedirects(self.client.post(path), reverse("studies:material_list"))
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(Subject.objects.filter(pk=self.subject.pk).exists())

    def test_material_rejects_unsafe_or_invalid_urls(self):
        for url in ("javascript:alert(1)", "ftp://example.com/file", "not a valid url"):
            with self.subTest(url=url):
                response = self.client.post(reverse("studies:material_create"), self.material_data(url=url))
                self.assertEqual(response.status_code, 200)
                self.assertIn("url", response.context["form"].errors)
                self.assertEqual(Material.objects.count(), 2)

    def test_material_search_filters_and_foreign_filter_validation(self):
        path = reverse("studies:material_list")
        response = self.client.get(path, {"q": "Python", "subject": self.subject.pk, "task": self.task.pk})
        self.assertEqual(list(response.context["object_list"]), [self.material])
        response = self.client.get(path, {"task": self.other_task.pk})
        self.assertIn("task", response.context["filter_form"].errors)
        self.assertEqual(list(response.context["object_list"]), [])

    def test_task_delete_keeps_material_with_subject(self):
        path = reverse("studies:task_delete", args=[self.task.pk])
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertRedirects(self.client.post(path), reverse("studies:task_list"))
        self.material.refresh_from_db()
        self.assertIsNone(self.material.task_id)
        self.assertEqual(self.material.subject_id, self.subject.pk)

    def test_csrf_protects_mutations_and_valid_token_allows_save(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for prefix, obj in (("subject", self.subject), ("task", self.task), ("material", self.material)):
            for action in ("create", "update", "delete"):
                args = [obj.pk] if action != "create" else []
                self.assertEqual(client.post(reverse(f"studies:{prefix}_{action}", args=args), {}).status_code, 403)
        path = reverse("studies:subject_create")
        client.get(path)
        response = client.post(path, {
            "name": "CSRF subject", "color": "#176b58",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertRedirects(response, reverse("studies:subject_list"))
        self.assertTrue(Subject.objects.filter(name="CSRF subject", owner=self.owner).exists())

    def test_database_enforces_time_priority_and_status_constraints(self):
        for changes in ({"estimated_minutes": 0}, {"priority": 9}, {"status": Task.Status.DONE}):
            with self.subTest(changes=changes):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Task.objects.filter(pk=self.task.pk).update(**changes)
        self.task.refresh_from_db()
        self.assertEqual(self.task.estimated_minutes, 180)
        self.assertEqual(self.task.status, Task.Status.TODO)
