from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from core.decorators import teacher_required
from .models import TeacherUser
from posts.models import Post, Like, Comment, Report, SavedPost, GenericFollow
from notifications.models import Notification
from posts.utils import get_annotated_posts
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from students.models import StudentUser
from core.utils import contains_profanity

def login_view(request):
    # If already logged in as a different role, clear that session so user can switch
    existing_role = request.session.get('role')
    if existing_role and existing_role != 'teacher':
        request.session.flush()
    # If already logged in as teacher, go to feed
    if request.session.get('role') == 'teacher' and request.session.get('teacher_id'):
        return redirect('teacher_feed')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            teacher = TeacherUser.objects.get(email=email)
            if teacher.is_blocked:
                messages.error(request, "Your account has been blocked. Contact admin.")
            elif check_password(password, teacher.password):
                request.session.flush()
                request.session['role'] = 'teacher'
                request.session['teacher_id'] = teacher.id
                return redirect('teacher_feed')
            else:
                messages.error(request, "Invalid credentials.")
        except TeacherUser.DoesNotExist:
            messages.error(request, "Invalid credentials.")
    return render(request, 'teachers/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('teacher_login')

@teacher_required
def feed_view(request):
    teacher_id = request.session['teacher_id']
    
    # Teachers see all student posts + own posts + admin posts
    posts_qs = Post.objects.filter(
        Q(author_role='student') |
        Q(author_role='teacher', author_id=teacher_id) |
        Q(author_role='admin')
    ).order_by('-created_at')

    all_posts = get_annotated_posts(posts_qs, 'teacher', teacher_id)
    pinned_posts = [p for p in all_posts if p.is_pin_active()]
    regular_posts = [p for p in all_posts if not p.is_pin_active()]
    
    final_feed = pinned_posts + regular_posts

    return render(request, 'teachers/feed.html', {'posts': final_feed})

@teacher_required
def explore_view(request):
    teacher_id = request.session['teacher_id']
    query = request.GET.get('q', '')
    
    # We want a list of students and teachers to follow instead of posts.
    people_results = []
    
    # Find IDs of users this teacher is already following
    following_students = GenericFollow.objects.filter(follower_role='teacher', follower_id=teacher_id, following_role='student').values_list('following_id', flat=True)
    following_teachers = GenericFollow.objects.filter(follower_role='teacher', follower_id=teacher_id, following_role='teacher').values_list('following_id', flat=True)
    
    if not query:
        # Show suggested people: random or recent
        students = StudentUser.objects.all().order_by('-created_at')[:20]
        teachers = TeacherUser.objects.exclude(id=teacher_id).order_by('-created_at')[:20]
    else:
        # Search by name or id
        students = StudentUser.objects.filter(
            Q(name__icontains=query) | Q(roll_number__icontains=query)
        )
        teachers = TeacherUser.objects.filter(
            Q(name__icontains=query) | Q(employee_id__icontains=query)
        ).exclude(id=teacher_id)
        
    for student in students:
        student.is_following = student.id in following_students
        student.user_role = 'student'
        people_results.append(student)
        
    for teacher in teachers:
        teacher.is_following = teacher.id in following_teachers
        teacher.user_role = 'teacher'
        people_results.append(teacher)
        
    context = {
        'query': query,
        'people_results': people_results,
    }
    return render(request, 'teachers/explore.html', context)

@teacher_required
def toggle_follow(request):
    if request.method == 'POST':
        teacher_id = request.session['teacher_id']
        following_role = request.POST.get('role')
        following_id = request.POST.get('id')
        
        if not following_role or not following_id:
            return JsonResponse({'error': 'Invalid data'}, status=400)
            
        follow = GenericFollow.objects.filter(
            follower_role='teacher', follower_id=teacher_id,
            following_role=following_role, following_id=following_id
        ).first()
        
        if follow:
            follow.delete()
            return JsonResponse({'following': False})
        else:
            GenericFollow.objects.create(
                follower_role='teacher', follower_id=teacher_id,
                following_role=following_role, following_id=following_id
            )
            # Send Notification
            Notification.objects.create(
                recipient_role=following_role,
                recipient_id=following_id,
                notif_type='follow',
                actor_role='teacher',
                actor_id=teacher_id,
                message="started following you"
            )
            return JsonResponse({'following': True})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@teacher_required
def post_create_view(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your post contains inappropriate language and cannot be published.")
            return redirect('teacher_feed')
            
        image = request.FILES.get('image')
        if image and image.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
            return redirect('teacher_feed')
        teacher_id = request.session['teacher_id']
        Post.objects.create(content=content, image=image, author_role='teacher', author_id=teacher_id)
        messages.success(request, "Post created successfully!")
    return redirect('teacher_feed')

@teacher_required
def post_detail_view(request, post_id):
    teacher_id = request.session['teacher_id']
    post = get_object_or_404(Post, id=post_id)
    posts_qs = Post.objects.filter(id=post_id)
    annotated_posts = get_annotated_posts(posts_qs, 'teacher', teacher_id)
    if not annotated_posts:
        return redirect('teacher_feed')
    return render(request, 'teachers/post_detail.html', {'post': annotated_posts[0]})

@teacher_required
def post_delete_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    teacher_id = request.session['teacher_id']
    # Teacher can delete student posts OR their own posts
    if post.author_role == 'student' or (post.author_role == 'teacher' and post.author_id == teacher_id):
        post.delete()
        messages.success(request, "Post deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'teacher_feed'))

@teacher_required
def post_edit_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author_role != 'teacher' or post.author_id != request.session['teacher_id']:
        return redirect('teacher_feed')
        
    if request.method == 'POST':
        content = request.POST.get('content', post.content)
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your post contains inappropriate language and cannot be published.")
            return render(request, 'teachers/post_edit.html', {'post': post})
        
        post.content = content
        if 'image' in request.FILES:
            image = request.FILES['image']
            if image.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
                return render(request, 'teachers/post_edit.html', {'post': post})
            post.image = image
        post.save()
        messages.success(request, "Post updated.")
        return redirect('teacher_post_detail', post_id=post.id)
    return render(request, 'teachers/post_edit.html', {'post': post})

@teacher_required
def like_view(request, post_id):
    if request.method == 'POST':
        teacher_id = request.session['teacher_id']
        post = get_object_or_404(Post, id=post_id)
        reaction_type = request.POST.get('reaction_type', 'like')
        like = Like.objects.filter(post=post, liker_role='teacher', liker_id=teacher_id).first()
        
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
            Like.objects.create(post=post, liker_role='teacher', liker_id=teacher_id, reaction_type=reaction_type)
            liked = True
            if not (post.author_role == 'teacher' and post.author_id == teacher_id):
                Notification.objects.create(
                    recipient_role=post.author_role,
                    recipient_id=post.author_id,
                    notif_type='like',
                    actor_role='teacher',
                    actor_id=teacher_id,
                    post=post,
                    message="reacted to your post"
                )
        
        count = post.likes.count()
        return JsonResponse({'liked': liked, 'count': count, 'reaction_type': reaction_type})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@teacher_required
def report_view(request, post_id):
    if request.method == 'POST':
        teacher_id = request.session['teacher_id']
        post = get_object_or_404(Post, id=post_id)
        reason = request.POST.get('reason', 'other')
        description = request.POST.get('description', '')
        existing = Report.objects.filter(post=post, reporter_role='teacher', reporter_id=teacher_id).first()
        if not existing:
            Report.objects.create(
                post=post,
                reporter_role='teacher',
                reporter_id=teacher_id,
                reason=reason,
                description=description
            )
            return JsonResponse({'success': True, 'message': 'Report submitted.'})
        return JsonResponse({'success': False, 'message': 'Already reported.'})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@teacher_required
def save_post_view(request, post_id):
    if request.method == 'POST':
        teacher_id = request.session['teacher_id']
        post = get_object_or_404(Post, id=post_id)
        saved = SavedPost.objects.filter(post=post, saver_role='teacher', saver_id=teacher_id).first()
        if saved:
            saved.delete()
            return JsonResponse({'saved': False})
        else:
            SavedPost.objects.create(post=post, saver_role='teacher', saver_id=teacher_id)
            return JsonResponse({'saved': True})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@teacher_required
def saved_posts_view(request):
    teacher_id = request.session['teacher_id']
    saved_ids = SavedPost.objects.filter(saver_role='teacher', saver_id=teacher_id).values_list('post_id', flat=True)
    posts_qs = Post.objects.filter(id__in=saved_ids).order_by('-created_at')
    posts = get_annotated_posts(posts_qs, 'teacher', teacher_id)
    for p in posts:
        p.is_saved = True
    return render(request, 'teachers/saved_posts.html', {'posts': posts})

@teacher_required
def comment_view(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your comment contains inappropriate language and cannot be published.")
            return redirect(request.META.get('HTTP_REFERER', 'teacher_feed'))
            
        teacher_id = request.session['teacher_id']
        post = get_object_or_404(Post, id=post_id)
        Comment.objects.create(post=post, author_role='teacher', author_id=teacher_id, content=content)
        
        if not (post.author_role == 'teacher' and post.author_id == teacher_id):
            Notification.objects.create(
                recipient_role=post.author_role,
                recipient_id=post.author_id,
                notif_type='comment',
                actor_role='teacher',
                actor_id=teacher_id,
                post=post,
                message="commented on your post"
            )
        messages.success(request, "Comment added.")
    return redirect(f"/teacher/post/{post_id}/")

@teacher_required
def comment_delete_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    teacher_id = request.session['teacher_id']
    # Teachers can delete their own comments or any student's comment
    if (comment.author_role == 'teacher' and comment.author_id == teacher_id) or comment.author_role == 'student':
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'teacher_feed'))

@teacher_required
def edit_profile_view(request):
    teacher = get_object_or_404(TeacherUser, id=request.session['teacher_id'])
    if request.method == 'POST':
        teacher.name = request.POST.get('name', teacher.name)
        teacher.department = request.POST.get('department', teacher.department)
        if 'profile_pic' in request.FILES:
            profile_pic = request.FILES['profile_pic']
            if profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
                return render(request, 'teachers/edit_profile.html', {'teacher': teacher})
            teacher.profile_pic = profile_pic
        teacher.save()
        messages.success(request, "Profile updated.")
        return redirect('teacher_feed')
    return render(request, 'teachers/edit_profile.html', {'teacher': teacher})

@teacher_required
def change_password_view(request):
    if request.method == 'POST':
        teacher = get_object_or_404(TeacherUser, id=request.session['teacher_id'])
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not check_password(current_password, teacher.password):
            messages.error(request, "Incorrect current password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            teacher.password = make_password(new_password)
            teacher.save()
            messages.success(request, "Password updated successfully.")
            return redirect('teacher_feed')
    return render(request, 'teachers/change_password.html')

@teacher_required
def notifications_view(request):
    teacher_id = request.session['teacher_id']
    notifs = Notification.objects.filter(recipient_role='teacher', recipient_id=teacher_id).order_by('-created_at')
    for n in notifs:
        n.is_read = True
        n.save()
    return render(request, 'teachers/notifications.html', {'notifications': notifs})

@teacher_required
def chat_view(request):
    teacher_id = request.session['teacher_id']
    query = request.GET.get('q', '')
    
    users = []
    
    if query:
        # Search for both students and teachers
        students = StudentUser.objects.filter(
            Q(name__icontains=query) | Q(roll_number__icontains=query)
        )
        teachers = TeacherUser.objects.filter(
            Q(name__icontains=query) | Q(employee_id__icontains=query)
        ).exclude(id=teacher_id)
        
        for s in students:
            s.user_role = 'student'
            users.append(s)
        for t in teachers:
            t.user_role = 'teacher'
            users.append(t)
    else:
        # Get users this teacher has chatted with
        from chat.models import DirectMessage
        sent_msgs = DirectMessage.objects.filter(sender_role='teacher', sender_id=teacher_id)
        recv_msgs = DirectMessage.objects.filter(receiver_role='teacher', receiver_id=teacher_id)
        
        chatted_with = set()
        for msg in sent_msgs:
            chatted_with.add((msg.receiver_role, msg.receiver_id))
        for msg in recv_msgs:
            chatted_with.add((msg.sender_role, msg.sender_id))
            
        for role, u_id in chatted_with:
            if role == 'student':
                user = StudentUser.objects.filter(id=u_id).first()
            elif role == 'teacher':
                user = TeacherUser.objects.filter(id=u_id).first()
            
            if user:
                user.user_role = role
                users.append(user)
                
    return render(request, 'teachers/chat_list.html', {'users': users, 'query': query})

@teacher_required
def chat_detail_view(request, role, user_id):
    teacher_id = request.session['teacher_id']
    from chat.models import DirectMessage
    
    if role == 'student':
        other_user = get_object_or_404(StudentUser, id=user_id)
    elif role == 'teacher':
        other_user = get_object_or_404(TeacherUser, id=user_id)
    else:
        return redirect('teacher_chat')
        
    other_user.user_role = role
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Profanity Check
            if contains_profanity(content):
                messages.error(request, "Your message contains inappropriate language and cannot be sent.")
                return redirect('teacher_chat_detail', role=role, user_id=user_id)
            DirectMessage.objects.create(
                sender_role='teacher', sender_id=teacher_id,
                receiver_role=role, receiver_id=user_id,
                content=content
            )
            return redirect('teacher_chat_detail', role=role, user_id=user_id)
            
    messages_list = DirectMessage.objects.filter(
        Q(sender_role='teacher', sender_id=teacher_id, receiver_role=role, receiver_id=user_id) |
        Q(sender_role=role, sender_id=user_id, receiver_role='teacher', receiver_id=teacher_id)
    ).order_by('timestamp')
    
    # Mark as read
    DirectMessage.objects.filter(
        sender_role=role, sender_id=user_id,
        receiver_role='teacher', receiver_id=teacher_id,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'other_user': other_user,
        'messages_list': messages_list
    }
    return render(request, 'teachers/chat_detail.html', context)
