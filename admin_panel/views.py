from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from core.decorators import admin_required
from .models import AdminUser
from students.models import StudentUser
from teachers.models import TeacherUser
from posts.models import Post, Comment, Report, Like, SavedPost
from posts.utils import get_annotated_posts
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
import json
from core.utils import contains_profanity

def login_view(request):
    # If already logged in as a different role, clear that session so user can switch
    existing_role = request.session.get('role')
    if existing_role and existing_role != 'admin':
        request.session.flush()
    # If already logged in as admin, go to dashboard
    if request.session.get('role') == 'admin' and request.session.get('admin_id'):
        return redirect('admin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            admin = AdminUser.objects.get(username=username)
            if check_password(password, admin.password):
                request.session.flush()
                request.session['role'] = 'admin'
                request.session['admin_id'] = admin.id
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Invalid credentials.")
        except AdminUser.DoesNotExist:
            messages.error(request, "Invalid credentials.")
    return render(request, 'admin_panel/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('admin_login')

@admin_required
def dashboard_view(request):
    admin_id = request.session['admin_id']
    
    total_students = StudentUser.objects.count()
    total_teachers = TeacherUser.objects.count()
    total_posts = Post.objects.count()
    
    now = timezone.now()
    active_pins = Post.objects.filter(is_pinned=True, pin_expires_at__gt=now).count()
    pending_reports = Report.objects.filter(status='pending').count()
    
    # Analytics: Posts per day (last 7 days)
    posts_per_day = []
    posts_per_day_labels = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = Post.objects.filter(created_at__date=day).count()
        posts_per_day.append(count)
        posts_per_day_labels.append(day.strftime('%b %d'))

    # Analytics: Reaction distribution
    reaction_counts = {}
    for choice in ['like', 'celebrate', 'insightful', 'funny']:
        reaction_counts[choice] = Like.objects.filter(reaction_type=choice).count()
    reaction_labels = list(reaction_counts.keys())
    reaction_values = list(reaction_counts.values())

    # Analytics: Top 5 liked posts
    top_posts = Post.objects.annotate(num_likes=Count('likes')).order_by('-num_likes')[:5]
    top_post_labels = [f"Post #{p.id}: {p.content[:20]}..." if len(p.content) > 20 else f"Post #{p.id}: {p.content}" for p in top_posts]
    top_post_values = [p.num_likes for p in top_posts]

    # Analytics: Active vs Blocked users
    active_students = StudentUser.objects.filter(is_blocked=False).count()
    blocked_students = StudentUser.objects.filter(is_blocked=True).count()
    active_teachers = TeacherUser.objects.filter(is_blocked=False).count()
    blocked_teachers = TeacherUser.objects.filter(is_blocked=True).count()

    posts_qs = Post.objects.all().order_by('-created_at')
    all_posts = get_annotated_posts(posts_qs, 'admin', admin_id)
    pinned_posts = [p for p in all_posts if p.is_pin_active()]
    regular_posts = [p for p in all_posts if not p.is_pin_active()]
    
    final_feed = pinned_posts + regular_posts
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_posts': total_posts,
        'active_pins': active_pins,
        'pending_reports': pending_reports,
        'posts': final_feed,
        # Analytics JSON
        'posts_per_day_labels': json.dumps(posts_per_day_labels),
        'posts_per_day_data': json.dumps(posts_per_day),
        'reaction_labels': json.dumps(reaction_labels),
        'reaction_values': json.dumps(reaction_values),
        'top_post_labels': json.dumps(top_post_labels),
        'top_post_values': json.dumps(top_post_values),
        'active_students': active_students,
        'blocked_students': blocked_students,
        'active_teachers': active_teachers,
        'blocked_teachers': blocked_teachers,
    }

    return render(request, 'admin_panel/dashboard.html', context)

@admin_required
def post_create_view(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your post contains inappropriate language and cannot be published.")
            return redirect('admin_dashboard')
        
        image = request.FILES.get('image')
        pin = request.POST.get('pin', '0')  # '1' = pinned announcement, '0' = regular post
        if image and image.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
            return redirect('admin_dashboard')
        admin_id = request.session['admin_id']
        if pin == '1':
            expires_at = timezone.now() + timedelta(hours=24)
            Post.objects.create(
                content=content,
                image=image,
                author_role='admin',
                author_id=admin_id,
                is_pinned=True,
                pin_expires_at=expires_at
            )
            messages.success(request, "Pinned announcement created (expires in 24h)!")
        else:
            Post.objects.create(
                content=content,
                image=image,
                author_role='admin',
                author_id=admin_id,
            )
            messages.success(request, "Post created successfully!")
    return redirect('admin_dashboard')

@admin_required
def post_detail_view(request, post_id):
    admin_id = request.session['admin_id']
    post = get_object_or_404(Post, id=post_id)
    posts_qs = Post.objects.filter(id=post_id)
    annotated_posts = get_annotated_posts(posts_qs, 'admin', admin_id)
    if not annotated_posts:
        return redirect('admin_dashboard')
    return render(request, 'admin_panel/post_detail.html', {'post': annotated_posts[0]})

@admin_required
def post_edit_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content', post.content)
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your post contains inappropriate language and cannot be published.")
            return render(request, 'admin_panel/post_edit.html', {'post': post})
        
        post.content = content
        if 'image' in request.FILES:
            image = request.FILES['image']
            if image.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
                return render(request, 'admin_panel/post_edit.html', {'post': post})
            post.image = image
        post.save()
        messages.success(request, "Post updated.")
        return redirect('admin_dashboard')
    return render(request, 'admin_panel/post_edit.html', {'post': post})

@admin_required
def post_delete_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect('admin_dashboard')

@admin_required
def comment_delete_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

@admin_required
def reports_view(request):
    status_filter = request.GET.get('status', 'pending')
    reports = Report.objects.filter(status=status_filter).order_by('-created_at')
    # Attach post author info
    for r in reports:
        try:
            if r.post.author_role == 'student':
                author = StudentUser.objects.get(id=r.post.author_id)
                r.post_author_name = author.name
            elif r.post.author_role == 'teacher':
                author = TeacherUser.objects.get(id=r.post.author_id)
                r.post_author_name = author.name
            else:
                r.post_author_name = 'Admin'
        except Exception:
            r.post_author_name = 'Unknown'
    return render(request, 'admin_panel/reports.html', {'reports': reports, 'status_filter': status_filter})

@admin_required
def resolve_report_view(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.status = 'resolved'
    report.save()
    messages.success(request, "Report resolved.")
    return redirect('admin_reports')

@admin_required
def dismiss_report_view(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.status = 'dismissed'
    report.save()
    messages.success(request, "Report dismissed.")
    return redirect('admin_reports')

@admin_required
def students_list_view(request):
    query = request.GET.get('q', '')
    if query:
        students = StudentUser.objects.filter(name__icontains=query) | StudentUser.objects.filter(roll_number__icontains=query)
    else:
        students = StudentUser.objects.all()
    return render(request, 'admin_panel/students_list.html', {'students': students, 'query': query})

@admin_required
def teachers_list_view(request):
    query = request.GET.get('q', '')
    if query:
        teachers = TeacherUser.objects.filter(name__icontains=query) | TeacherUser.objects.filter(employee_id__icontains=query)
    else:
        teachers = TeacherUser.objects.all()
    return render(request, 'admin_panel/teachers_list.html', {'teachers': teachers, 'query': query})

@admin_required
def block_student_view(request, user_id):
    student = get_object_or_404(StudentUser, id=user_id)
    student.is_blocked = True
    student.save()
    messages.success(request, f"Student {student.name} blocked.")
    return redirect('admin_students_list')

@admin_required
def unblock_student_view(request, user_id):
    student = get_object_or_404(StudentUser, id=user_id)
    student.is_blocked = False
    student.save()
    messages.success(request, f"Student {student.name} unblocked.")
    return redirect('admin_students_list')

@admin_required
def delete_student_view(request, user_id):
    student = get_object_or_404(StudentUser, id=user_id)
    student.delete()
    messages.success(request, "Student deleted.")
    return redirect('admin_students_list')

@admin_required
def add_student_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        bio = request.POST.get('bio', '').strip()
        profile_pic = request.FILES.get('profile_pic')

        errors = []
        if not name:
            errors.append('Name is required.')
        if not roll_number:
            errors.append('Roll number is required.')
        if not email:
            errors.append('Email is required.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append('Enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if StudentUser.objects.filter(roll_number=roll_number).exists():
            errors.append('A student with this roll number already exists.')
        if StudentUser.objects.filter(email=email).exists():
            errors.append('A student with this email already exists.')
        if profile_pic and profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            errors.append('Only JPEG, PNG, GIF, and WEBP images are allowed.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('admin_students_list')

        student = StudentUser(
            name=name,
            roll_number=roll_number,
            email=email,
            password=make_password(password),
            bio=bio,
        )
        if profile_pic:
            student.profile_pic = profile_pic
        student.save()
        messages.success(request, f"Student '{name}' added successfully.")
        return redirect('admin_students_list')
    return redirect('admin_students_list')

@admin_required
def block_teacher_view(request, user_id):
    teacher = get_object_or_404(TeacherUser, id=user_id)
    teacher.is_blocked = True
    teacher.save()
    messages.success(request, f"Teacher {teacher.name} blocked.")
    return redirect('admin_teachers_list')

@admin_required
def unblock_teacher_view(request, user_id):
    teacher = get_object_or_404(TeacherUser, id=user_id)
    teacher.is_blocked = False
    teacher.save()
    messages.success(request, f"Teacher {teacher.name} unblocked.")
    return redirect('admin_teachers_list')

@admin_required
def delete_teacher_view(request, user_id):
    teacher = get_object_or_404(TeacherUser, id=user_id)
    teacher.delete()
    messages.success(request, "Teacher deleted.")
    return redirect('admin_teachers_list')

@admin_required
def add_teacher_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        email = request.POST.get('email', '').strip()
        department = request.POST.get('department', '').strip()
        password = request.POST.get('password', '').strip()
        profile_pic = request.FILES.get('profile_pic')

        errors = []
        if not name:
            errors.append('Name is required.')
        if not employee_id:
            errors.append('Employee ID is required.')
        if not email:
            errors.append('Email is required.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append('Enter a valid email address.')
        if not department:
            errors.append('Department is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if TeacherUser.objects.filter(employee_id=employee_id).exists():
            errors.append('A teacher with this Employee ID already exists.')
        if TeacherUser.objects.filter(email=email).exists():
            errors.append('A teacher with this email already exists.')
        if profile_pic and profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            errors.append('Only JPEG, PNG, GIF, and WEBP images are allowed.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('admin_teachers_list')

        teacher = TeacherUser(
            name=name,
            employee_id=employee_id,
            email=email,
            department=department,
            password=make_password(password),
        )
        if profile_pic:
            teacher.profile_pic = profile_pic
        try:
            teacher.save()
            messages.success(request, f"Teacher '{name}' added successfully.")
        except Exception:
            messages.error(request, "A teacher with this email or Employee ID already exists.")
        return redirect('admin_teachers_list')
    return redirect('admin_teachers_list')

@admin_required
def edit_profile_view(request):
    admin = get_object_or_404(AdminUser, id=request.session['admin_id'])
    if request.method == 'POST':
        admin.username = request.POST.get('username', admin.username)
        admin.email = request.POST.get('email', admin.email)
        if 'profile_pic' in request.FILES:
            profile_pic = request.FILES['profile_pic']
            if profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
                return render(request, 'admin_panel/edit_profile.html', {'admin': admin})
            admin.profile_pic = profile_pic
        admin.save()
        messages.success(request, "Profile updated.")
        return redirect('admin_dashboard')
    return render(request, 'admin_panel/edit_profile.html', {'admin': admin})

@admin_required
def change_password_view(request):
    if request.method == 'POST':
        admin = get_object_or_404(AdminUser, id=request.session['admin_id'])
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not check_password(current_password, admin.password):
            messages.error(request, "Incorrect current password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            admin.password = make_password(new_password)
            admin.save()
            messages.success(request, "Password updated successfully.")
            return redirect('admin_dashboard')
    return render(request, 'admin_panel/change_password.html')

@admin_required
def like_view(request, post_id):
    if request.method == 'POST':
        admin_id = request.session['admin_id']
        post = get_object_or_404(Post, id=post_id)
        reaction_type = request.POST.get('reaction_type', 'like')
        like = Like.objects.filter(post=post, liker_role='admin', liker_id=admin_id).first()
        
        if like:
            if like.reaction_type == reaction_type:
                like.delete()
                liked = False
                reaction_type = None
            else:
                like.reaction_type = reaction_type
                like.save()
                liked = True
        else:
            Like.objects.create(post=post, liker_role='admin', liker_id=admin_id, reaction_type=reaction_type)
            liked = True
        
        count = post.likes.count()
        return JsonResponse({'liked': liked, 'count': count, 'reaction_type': reaction_type})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@admin_required
def comment_view(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your comment contains inappropriate language and cannot be published.")
            return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))
        
        admin_id = request.session['admin_id']
        post = get_object_or_404(Post, id=post_id)
        Comment.objects.create(post=post, author_role='admin', author_id=admin_id, content=content)
        messages.success(request, "Comment added.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))
