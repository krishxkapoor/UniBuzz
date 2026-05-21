from django.shortcuts import render, redirect

def landing_view(request):
    role = request.session.get('role')
    if role == 'student':
        return redirect('student_feed')
    elif role == 'teacher':
        return redirect('teacher_feed')
    elif role == 'admin':
        return redirect('admin_dashboard')
    return render(request, 'landing.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)
