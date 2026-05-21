from posts.models import Post, Like, Comment, SavedPost
from students.models import StudentUser
from teachers.models import TeacherUser
from admin_panel.models import AdminUser
from django.db.models import Count

def get_annotated_posts(post_qs, current_role=None, current_user_id=None):
    """
    Takes a queryset of Posts and adds:
    - author_name
    - author_pic_url
    - like_count
    - comment_count
    - is_liked (by current user)
    - reaction_type (current user's reaction)
    - is_saved (by current user)
    """
    posts = list(post_qs)
    
    # Pre-fetch all authors to avoid N+1 queries
    student_ids = [p.author_id for p in posts if p.author_role == 'student']
    teacher_ids = [p.author_id for p in posts if p.author_role == 'teacher']
    admin_ids = [p.author_id for p in posts if p.author_role == 'admin']

    students = {s.id: s for s in StudentUser.objects.filter(id__in=student_ids)}
    teachers = {t.id: t for t in TeacherUser.objects.filter(id__in=teacher_ids)}
    admins = {a.id: a for a in AdminUser.objects.filter(id__in=admin_ids)}

    # Pre-fetch likes and comments count
    post_ids = [p.id for p in posts]
    likes = Like.objects.filter(post_id__in=post_ids)
    comments = Comment.objects.filter(post_id__in=post_ids)

    like_counts = {}
    for l in likes:
        like_counts[l.post_id] = like_counts.get(l.post_id, 0) + 1

    comment_counts = {}
    for c in comments:
        comment_counts[c.post_id] = comment_counts.get(c.post_id, 0) + 1

    user_likes = {}  # post_id -> reaction_type
    user_saved = set()
    if current_role and current_user_id:
        user_like_qs = Like.objects.filter(
            post_id__in=post_ids, 
            liker_role=current_role, 
            liker_id=current_user_id
        )
        for like in user_like_qs:
            user_likes[like.post_id] = like.reaction_type

        user_saved = set(SavedPost.objects.filter(
            post_id__in=post_ids,
            saver_role=current_role,
            saver_id=current_user_id
        ).values_list('post_id', flat=True))

    for p in posts:
        if p.author_role == 'student':
            author = students.get(p.author_id)
        elif p.author_role == 'teacher':
            author = teachers.get(p.author_id)
        else:
            author = admins.get(p.author_id)

        if author:
            p.author_name = getattr(author, 'name', getattr(author, 'username', 'Unknown'))
            p.author_pic_url = author.profile_pic.url if author.profile_pic else None
        else:
            p.author_name = 'Unknown'
            p.author_pic_url = None

        p.like_count = like_counts.get(p.id, 0)
        p.comment_count = comment_counts.get(p.id, 0)
        p.is_liked = p.id in user_likes
        p.reaction_type = user_likes.get(p.id, 'like')
        p.is_saved = p.id in user_saved

    return posts
