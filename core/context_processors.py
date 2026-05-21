from django.db.models import Count
import random
from students.models import StudentUser
from teachers.models import TeacherUser
from posts.models import GenericFollow

def global_suggestions(request):
    """
    Provides a global list of suggested users ('People to Follow') to the base template.
    Returns 5 random users (mix of students and teachers) that the current user is NOT following.
    """
    role = request.session.get('role')
    user_id = request.session.get(f'{role}_id')
    
    if not role or not user_id:
        return {'suggested_users': []}

    # Get IDs of users already followed by the current user
    following_student_ids = GenericFollow.objects.filter(
        follower_role=role, follower_id=user_id, following_role='student'
    ).values_list('following_id', flat=True)
    
    following_teacher_ids = GenericFollow.objects.filter(
        follower_role=role, follower_id=user_id, following_role='teacher'
    ).values_list('following_id', flat=True)

    # Base querysets
    student_qs = StudentUser.objects.all()
    teacher_qs = TeacherUser.objects.all()

    # Exclude current user and already followed users
    if role == 'student':
        student_qs = student_qs.exclude(id=user_id)
    elif role == 'teacher':
        teacher_qs = teacher_qs.exclude(id=user_id)
        
    student_qs = student_qs.exclude(id__in=following_student_ids)
    teacher_qs = teacher_qs.exclude(id__in=following_teacher_ids)

    # To get a mix, we can fetch all remaining IDs, combine, and pick 5 at random, 
    # but for simplicity, we'll fetch a limited number from each and combine.
    # Note: For production with large DBs, using random order (?) can be slow, 
    # but we'll use order_by('-id') to get the newest users for simplicity.
    
    students = list(student_qs.order_by('-id')[:10])
    for s in students:
        s.user_role = 'student'
        s.display_id = s.roll_number
        
    teachers = list(teacher_qs.order_by('-id')[:10])
    for t in teachers:
        t.user_role = 'teacher'
        t.display_id = t.employee_id
        
    combined = students + teachers
    random.shuffle(combined)
    
    return {
        'suggested_users': combined[:5]
    }
