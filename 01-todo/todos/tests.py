from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import Todo
from .forms import TodoForm


class TodoModelTest(TestCase):
    def setUp(self):
        self.todo = Todo.objects.create(
            title="Test Todo",
            description="Test description",
            due_date=date.today() + timedelta(days=7)
        )

    def test_todo_creation(self):
        self.assertEqual(self.todo.title, "Test Todo")
        self.assertEqual(self.todo.description, "Test description")
        self.assertIsNotNone(self.todo.due_date)
        self.assertFalse(self.todo.is_resolved)

    def test_todo_default_is_resolved(self):
        new_todo = Todo.objects.create(title="Another Todo")
        self.assertFalse(new_todo.is_resolved)

    def test_todo_str_method(self):
        self.assertEqual(str(self.todo), "Test Todo")

    def test_todo_ordering(self):
        older_todo = Todo.objects.create(title="Older Todo")
        todos = Todo.objects.all()
        self.assertEqual(todos[0].title, "Older Todo")
        self.assertEqual(todos[1].title, "Test Todo")

    def test_todo_optional_fields(self):
        minimal_todo = Todo.objects.create(title="Minimal")
        self.assertIsNone(minimal_todo.description)
        self.assertIsNone(minimal_todo.due_date)


class TodoListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('todo_list')
        Todo.objects.create(title="Todo 1", description="First todo")
        Todo.objects.create(title="Todo 2", is_resolved=True)

    def test_list_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'todos/todo_list.html')

    def test_list_view_contains_todos(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Todo 1")
        self.assertContains(response, "Todo 2")

    def test_list_view_context(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['todos']), 2)


class TodoCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('todo_create')

    def test_create_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_view_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'todos/todo_form.html')

    def test_create_todo_with_valid_data(self):
        data = {
            'title': 'New Todo',
            'description': 'New description',
            'due_date': date.today() + timedelta(days=5)
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Todo.objects.count(), 1)
        self.assertEqual(Todo.objects.first().title, 'New Todo')

    def test_create_todo_without_optional_fields(self):
        data = {'title': 'Minimal Todo'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Todo.objects.count(), 1)

    def test_create_todo_without_title_fails(self):
        data = {'description': 'No title'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Todo.objects.count(), 0)


class TodoUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.todo = Todo.objects.create(
            title="Original Title",
            description="Original description"
        )
        self.url = reverse('todo_update', kwargs={'pk': self.todo.pk})

    def test_update_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_view_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'todos/todo_form.html')

    def test_update_todo_title(self):
        data = {
            'title': 'Updated Title',
            'description': 'Original description',
            'is_resolved': False
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.title, 'Updated Title')

    def test_update_todo_mark_resolved(self):
        data = {
            'title': 'Original Title',
            'description': 'Original description',
            'is_resolved': True
        }
        response = self.client.post(self.url, data)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.is_resolved)


class TodoDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.todo = Todo.objects.create(title="To Delete")
        self.url = reverse('todo_delete', kwargs={'pk': self.todo.pk})

    def test_delete_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_delete_view_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'todos/todo_confirm_delete.html')

    def test_delete_todo(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Todo.objects.count(), 0)


class TodoToggleResolvedTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.todo = Todo.objects.create(title="Toggle Test", is_resolved=False)
        self.url = reverse('todo_toggle', kwargs={'pk': self.todo.pk})

    def test_toggle_resolved_from_false_to_true(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.is_resolved)

    def test_toggle_resolved_from_true_to_false(self):
        self.todo.is_resolved = True
        self.todo.save()
        response = self.client.get(self.url)
        self.todo.refresh_from_db()
        self.assertFalse(self.todo.is_resolved)


class TodoFormTest(TestCase):
    def test_form_valid_with_all_fields(self):
        form_data = {
            'title': 'Test Title',
            'description': 'Test description',
            'due_date': date.today(),
            'is_resolved': False
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_required_fields_only(self):
        form_data = {'title': 'Test Title'}
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_title(self):
        form_data = {'description': 'No title'}
        form = TodoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_widget_types(self):
        form = TodoForm()
        self.assertEqual(form.fields['due_date'].widget.input_type, 'date')
