"""
Views for scheduler_ui app.
"""
from django.shortcuts import render


def index(request):
    """Configuration page."""
    return render(request, 'index.html')


def groups(request):
    """Groups management page."""
    return render(request, 'groups.html')


def generate(request):
    """Timetable generation and display page."""
    return render(request, 'timetable.html')
