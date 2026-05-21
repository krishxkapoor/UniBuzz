from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from core.decorators import student_required
from .models import StudentUser, Follow
from teachers.models import TeacherUser
from posts.models import Post, Like, Comment, Report, SavedPost, GenericFollow
from chat.models import DirectMessage, Group, GroupMessage
from notifications.models import Notification
from posts.utils import get_annotated_posts
from django.db.models import Q, Count
from django.utils import timezone
from core.utils import contains_profanity

def login_view(request):
    # If already logged in as a different role, clear that session so user can switch
    existing_role = request.session.get('role')
    if existing_role and existing_role != 'student':
        request.session.flush()
    # If already logged in as student, go to feed
    if request.session.get('role') == 'student' and request.session.get('student_id'):
        return redirect('student_feed')
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        password = request.POST.get('password')
        try:
            student = StudentUser.objects.get(roll_number=roll_number)
            if student.is_blocked:
                messages.error(request, "Your account has been blocked. Contact admin.")
            elif check_password(password, student.password):
                request.session.flush()
                request.session['role'] = 'student'
                request.session['student_id'] = student.id
                return redirect('student_feed')
            else:
                messages.error(request, "Invalid credentials.")
        except StudentUser.DoesNotExist:
            messages.error(request, "Invalid credentials.")
    return render(request, 'students/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('student_login')

@student_required
def feed_view(request):
    student_id = request.session['student_id']
    following_ids = Follow.objects.filter(follower_id=student_id).values_list('following_id', flat=True)
    
    posts_qs = Post.objects.filter(
        Q(author_role='student', author_id=student_id) |
        Q(author_role='student', author_id__in=following_ids) |
        Q(author_role='teacher') |
        Q(author_role='admin')
    ).order_by('-created_at')

    # Manual filtering for pinned posts to show at top
    all_posts = get_annotated_posts(posts_qs, 'student', student_id)
    pinned_posts = [p for p in all_posts if p.is_pin_active()]
    regular_posts = [p for p in all_posts if not p.is_pin_active()]
    
    final_feed = pinned_posts + regular_posts

    return render(request, 'students/feed.html', {'posts': final_feed})

@student_required
def explore_view(request):
    student_id = request.session['student_id']
    query = request.GET.get('q', '')
    
    suggested_students = []
    people_results = []
    post_results = []
    
    if not query:
        following_ids = Follow.objects.filter(follower_id=student_id).values_list('following_id', flat=True)
        suggested_students = StudentUser.objects.exclude(id=student_id).exclude(id__in=following_ids).annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:20]
    else:
        people_qs = StudentUser.objects.filter(
            Q(name__icontains=query) | Q(roll_number__icontains=query)
        ).annotate(followers_count=Count('followers')).exclude(id=student_id)
        
        following_ids = set(Follow.objects.filter(follower_id=student_id).values_list('following_id', flat=True))
        people_results = list(people_qs)
        for p in people_results:
            p.is_following = p.id in following_ids
        
        posts_qs = Post.objects.filter(content__icontains=query).order_by('-created_at')
        post_results = get_annotated_posts(posts_qs, 'student', student_id)
        
    context = {
        'query': query,
        'suggested_students': suggested_students,
        'people_results': people_results,
        'post_results': post_results,
        'current_student_id': student_id
    }
    return render(request, 'students/explore.html', context)

@student_required
def post_create_view(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your post contains inappropriate language and cannot be published.")
            return redirect('student_feed')
            
        image = request.FILES.get('image')
        if image and image.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
            return redirect('student_feed')
        student_id = request.session['student_id']
        Post.objects.create(content=content, image=image, author_role='student', author_id=student_id)
        messages.success(request, "Post created successfully!")
    return redirect('student_feed')

@student_required
def post_detail_view(request, post_id):
    student_id = request.session['student_id']
    post = get_object_or_404(Post, id=post_id)
    # Using the same utility logic to annotate the single post
    posts_qs = Post.objects.filter(id=post_id)
    annotated_posts = get_annotated_posts(posts_qs, 'student', student_id)
    if not annotated_posts:
        return redirect('student_feed')
    return render(request, 'students/post_detail.html', {'post': annotated_posts[0]})

@student_required
def post_delete_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author_role == 'student' and post.author_id == request.session['student_id']:
        post.delete()
        messages.success(request, "Post deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'student_feed'))

@student_required
def post_edit_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author_role != 'student' or post.author_id != request.session['student_id']:
        return redirect('student_feed')
        
    if request.method == 'POST':
        content = request.POST.get('content', post.content)
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your post contains inappropriate language and cannot be published.")
            return render(request, 'students/post_edit.html', {'post': post})
        
        post.content = content
        if 'image' in request.FILES:
            image = request.FILES['image']
            if image.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
                return render(request, 'students/post_edit.html', {'post': post})
            post.image = image
        post.save()
        messages.success(request, "Post updated.")
        return redirect('student_post_detail', post_id=post.id)
    return render(request, 'students/post_edit.html', {'post': post})

@student_required
def like_view(request, post_id):
    if request.method == 'POST':
        student_id = request.session['student_id']
        post = get_object_or_404(Post, id=post_id)
        reaction_type = request.POST.get('reaction_type', 'like')
        like = Like.objects.filter(post=post, liker_role='student', liker_id=student_id).first()
        
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
            Like.objects.create(post=post, liker_role='student', liker_id=student_id, reaction_type=reaction_type)
            liked = True
            if not (post.author_role == 'student' and post.author_id == student_id):
                Notification.objects.create(
                    recipient_role=post.author_role,
                    recipient_id=post.author_id,
                    notif_type='like',
                    actor_role='student',
                    actor_id=student_id,
                    post=post,
                    message=f"reacted to your post"
                )
        
        count = post.likes.count()
        return JsonResponse({'liked': liked, 'count': count, 'reaction_type': reaction_type})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@student_required
def report_view(request, post_id):
    if request.method == 'POST':
        student_id = request.session['student_id']
        post = get_object_or_404(Post, id=post_id)
        reason = request.POST.get('reason', 'other')
        description = request.POST.get('description', '')
        existing = Report.objects.filter(post=post, reporter_role='student', reporter_id=student_id).first()
        if not existing:
            Report.objects.create(
                post=post,
                reporter_role='student',
                reporter_id=student_id,
                reason=reason,
                description=description
            )
            return JsonResponse({'success': True, 'message': 'Report submitted.'})
        return JsonResponse({'success': False, 'message': 'Already reported.'})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@student_required
def save_post_view(request, post_id):
    if request.method == 'POST':
        student_id = request.session['student_id']
        post = get_object_or_404(Post, id=post_id)
        saved = SavedPost.objects.filter(post=post, saver_role='student', saver_id=student_id).first()
        if saved:
            saved.delete()
            return JsonResponse({'saved': False})
        else:
            SavedPost.objects.create(post=post, saver_role='student', saver_id=student_id)
            return JsonResponse({'saved': True})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@student_required
def saved_posts_view(request):
    student_id = request.session['student_id']
    saved_ids = SavedPost.objects.filter(saver_role='student', saver_id=student_id).values_list('post_id', flat=True)
    posts_qs = Post.objects.filter(id__in=saved_ids).order_by('-created_at')
    posts = get_annotated_posts(posts_qs, 'student', student_id)
    # Attach is_saved flag
    for p in posts:
        p.is_saved = True
    return render(request, 'students/saved_posts.html', {'posts': posts})

@student_required
def comment_view(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your comment contains inappropriate language and cannot be published.")
            return redirect(request.META.get('HTTP_REFERER', 'student_feed'))
            
        student_id = request.session['student_id']
        post = get_object_or_404(Post, id=post_id)
        Comment.objects.create(post=post, author_role='student', author_id=student_id, content=content)
        
        if not (post.author_role == 'student' and post.author_id == student_id):
            Notification.objects.create(
                recipient_role=post.author_role,
                recipient_id=post.author_id,
                notif_type='comment',
                actor_role='student',
                actor_id=student_id,
                post=post,
                message="commented on your post"
            )
        messages.success(request, "Comment added.")
    return redirect(f"/student/post/{post_id}/")

@student_required
def comment_delete_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author_role == 'student' and comment.author_id == request.session['student_id']:
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'student_feed'))

@student_required
def follow_view(request, user_id):
    student_id = request.session['student_id']
    if student_id != user_id:
        Follow.objects.get_or_create(follower_id=student_id, following_id=user_id)
        Notification.objects.create(
            recipient_role='student',
            recipient_id=user_id,
            notif_type='follow',
            actor_role='student',
            actor_id=student_id,
            message="started following you"
        )
    return redirect(request.META.get('HTTP_REFERER', 'student_feed'))

@student_required
def unfollow_view(request, user_id):
    student_id = request.session['student_id']
    Follow.objects.filter(follower_id=student_id, following_id=user_id).delete()
    return redirect(request.META.get('HTTP_REFERER', 'student_feed'))

@student_required
def toggle_follow(request):
    if request.method == 'POST':
        student_id = request.session['student_id']
        following_role = request.POST.get('role')
        following_id = request.POST.get('id')
        
        if not following_role or not following_id:
            return JsonResponse({'error': 'Invalid data'}, status=400)
            
        follow = GenericFollow.objects.filter(
            follower_role='student', follower_id=student_id,
            following_role=following_role, following_id=following_id
        ).first()
        
        if follow:
            follow.delete()
            return JsonResponse({'following': False})
        else:
            GenericFollow.objects.create(
                follower_role='student', follower_id=student_id,
                following_role=following_role, following_id=following_id
            )
            Notification.objects.create(
                recipient_role=following_role,
                recipient_id=following_id,
                notif_type='follow',
                actor_role='student',
                actor_id=student_id,
                message="started following you"
            )
            return JsonResponse({'following': True})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@student_required
def profile_view(request, user_id):
    student = get_object_or_404(StudentUser, id=user_id)
    current_student_id = request.session['student_id']
    
    posts_qs = Post.objects.filter(author_role='student', author_id=user_id).order_by('-created_at')
    posts = get_annotated_posts(posts_qs, 'student', current_student_id)
    
    followers_count = Follow.objects.filter(following=student).count()
    following_count = Follow.objects.filter(follower=student).count()
    is_following = Follow.objects.filter(follower_id=current_student_id, following=student).exists()
    
    context = {
        'profile_user': student,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_own_profile': current_student_id == student.id
    }
    return render(request, 'students/profile.html', context)

@student_required
def edit_profile_view(request):
    student = get_object_or_404(StudentUser, id=request.session['student_id'])
    if request.method == 'POST':
        student.name = request.POST.get('name', student.name)
        student.bio = request.POST.get('bio', student.bio)
        if 'profile_pic' in request.FILES:
            profile_pic = request.FILES['profile_pic']
            if profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
                return render(request, 'students/edit_profile.html', {'student': student})
            student.profile_pic = profile_pic
        student.save()
        messages.success(request, "Profile updated.")
        return redirect('student_profile', user_id=student.id)
    return render(request, 'students/edit_profile.html', {'student': student})

@student_required
def change_password_view(request):
    if request.method == 'POST':
        student = get_object_or_404(StudentUser, id=request.session['student_id'])
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not check_password(current_password, student.password):
            messages.error(request, "Incorrect current password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            student.password = make_password(new_password)
            student.save()
            messages.success(request, "Password updated successfully.")
            return redirect('student_profile', user_id=student.id)
    return render(request, 'students/change_password.html')

@student_required
def chat_view(request):
    student_id = request.session['student_id']
    query = request.GET.get('q', '')
    
    if query:
        users = StudentUser.objects.filter(
            Q(name__icontains=query) | Q(roll_number__icontains=query)
        ).exclude(id=student_id)
    else:
        # Get users this student has chatted with
        sent_msgs = DirectMessage.objects.filter(sender_role='student', sender_id=student_id).values_list('receiver_id', flat=True)
        recv_msgs = DirectMessage.objects.filter(receiver_role='student', receiver_id=student_id).values_list('sender_id', flat=True)
        chatted_ids = set(sent_msgs) | set(recv_msgs)
        users = StudentUser.objects.filter(id__in=chatted_ids)
        
    return render(request, 'students/chat_list.html', {'users': users, 'query': query})

@student_required
def chat_detail_view(request, user_id):
    student_id = request.session['student_id']
    other_student = get_object_or_404(StudentUser, id=user_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Profanity Check
            if contains_profanity(content):
                messages.error(request, "Your message contains inappropriate language and cannot be sent.")
                return redirect('student_chat_detail', user_id=user_id)
            DirectMessage.objects.create(
                sender_role='student', sender_id=student_id,
                receiver_role='student', receiver_id=user_id,
                content=content
            )
            return redirect('student_chat_detail', user_id=user_id)
            
    messages_list = DirectMessage.objects.filter(
        Q(sender_role='student', sender_id=student_id, receiver_role='student', receiver_id=user_id) |
        Q(sender_role='student', sender_id=user_id, receiver_role='student', receiver_id=student_id)
    ).order_by('timestamp')
    
    # Mark as read
    DirectMessage.objects.filter(
        sender_role='student', sender_id=user_id, receiver_role='student', receiver_id=student_id, is_read=False
    ).update(is_read=True)
    
    return render(request, 'students/chat_detail.html', {'other_student': other_student, 'messages_list': messages_list})

@student_required
def groups_view(request):
    student_id = request.session['student_id']
    groups = Group.objects.filter(members__id=student_id)
    return render(request, 'students/groups.html', {'groups': groups})

@student_required
def group_create_view(request):
    student = get_object_or_404(StudentUser, id=request.session['student_id'])
    if request.method == 'POST':
        name = request.POST.get('name')
        member_ids = request.POST.getlist('members')
        group_pic = request.FILES.get('group_pic')
        if group_pic and group_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            messages.error(request, 'Only JPEG, PNG, GIF, and WEBP images are allowed.')
            all_students = StudentUser.objects.exclude(id=student.id)
            return render(request, 'students/groups_create.html', {'all_students': all_students})
        
        group = Group.objects.create(name=name, created_by=student, group_pic=group_pic)
        group.members.add(student)
        for mid in member_ids:
            group.members.add(mid)
        messages.success(request, "Group created.")
        return redirect('student_groups')
        
    all_students = StudentUser.objects.exclude(id=student.id)
    return render(request, 'students/groups_create.html', {'all_students': all_students})

@student_required
def group_detail_view(request, group_id):
    group = get_object_or_404(Group, id=group_id, members__id=request.session['student_id'])
    messages_list = group.messages.all().order_by('timestamp')
    return render(request, 'students/group_detail.html', {'group': group, 'messages_list': messages_list})

@student_required
def group_send_view(request, group_id):
    student = get_object_or_404(StudentUser, id=request.session['student_id'])
    group = get_object_or_404(Group, id=group_id, members=student)
    if request.method == 'POST':
        content = request.POST.get('content')
        # Profanity Check
        if contains_profanity(content):
            messages.error(request, "Your message contains inappropriate language and cannot be sent.")
            return redirect('student_group_detail', group_id=group_id)
        GroupMessage.objects.create(group=group, sender=student, content=content)
    return redirect('student_group_detail', group_id=group_id)

@student_required
def notifications_view(request):
    student_id = request.session['student_id']
    notifs = Notification.objects.filter(recipient_role='student', recipient_id=student_id).order_by('-created_at')
    # Pre-fetch actor data could be done here similar to posts
    # Simplification: we will pass the list to template
    for n in notifs:
        n.is_read = True
        n.save()
    return render(request, 'students/notifications.html', {'notifications': notifs})
