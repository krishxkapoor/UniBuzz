from functools import wraps
from django.shortcuts import redirect

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('role') == 'student' and request.session.get('student_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/student/login/')
    return _wrapped_view

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('role') == 'teacher' and request.session.get('teacher_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/teacher/login/')
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('role') == 'admin' and request.session.get('admin_id'):
            return view_func(request, *args, **kwargs)
        return redirect('/admin-panel/login/')
    return _wrapped_view
