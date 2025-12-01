from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Todo
from .forms import TodoForm

class TodoListView(ListView):
    model = Todo
    template_name = 'todos/todo_list.html'
    context_object_name = 'todos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_todos = self.get_queryset().count()
        resolved_todos = self.get_queryset().filter(is_resolved=True).count()
        context['total_todos'] = total_todos
        context['resolved_todos'] = resolved_todos
        context['completion_percentage'] = int((resolved_todos / total_todos * 100)) if total_todos > 0 else 0
        return context

class TodoCreateView(CreateView):
    model = Todo
    template_name = 'todos/todo_form.html'
    form_class = TodoForm
    success_url = reverse_lazy('todo_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields.pop('is_resolved', None)
        return form

class TodoUpdateView(UpdateView):
    model = Todo
    template_name = 'todos/todo_form.html'
    form_class = TodoForm
    success_url = reverse_lazy('todo_list')

class TodoDeleteView(DeleteView):
    model = Todo
    template_name = 'todos/todo_confirm_delete.html'
    success_url = reverse_lazy('todo_list')

def toggle_resolved(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.is_resolved = not todo.is_resolved
    todo.save()
    return redirect('todo_list')
