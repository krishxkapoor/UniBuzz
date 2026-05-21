from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from admin_panel.models import AdminUser
from teachers.models import TeacherUser
from students.models import StudentUser, Follow
from posts.models import Post
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds initial data for the college social app'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1 AdminUser
        AdminUser.objects.all().delete()
        admin = AdminUser.objects.create(
            username='admin',
            email='admin@campus.edu',
            password=make_password('admin123')
        )

        # 2 TeacherUsers
        TeacherUser.objects.all().delete()
        t1 = TeacherUser.objects.create(
            employee_id='T001',
            name='Dr. Alice Smith',
            email='alice@campus.edu',
            department='Computer Science',
            password=make_password('teacher123')
        )
        t2 = TeacherUser.objects.create(
            employee_id='T002',
            name='Prof. Bob Jones',
            email='bob@campus.edu',
            department='Mathematics',
            password=make_password('teacher123')
        )

        # 5 StudentUsers
        StudentUser.objects.all().delete()
        s1 = StudentUser.objects.create(roll_number='CS2021001', name='John Doe', email='john@student.edu', password=make_password('student123'))
        s2 = StudentUser.objects.create(roll_number='CS2021002', name='Jane Roe', email='jane@student.edu', password=make_password('student123'))
        s3 = StudentUser.objects.create(roll_number='CS2021003', name='Mike Ross', email='mike@student.edu', password=make_password('student123'))
        s4 = StudentUser.objects.create(roll_number='CS2021004', name='Rachel Zane', email='rachel@student.edu', password=make_password('student123'))
        s5 = StudentUser.objects.create(roll_number='CS2021005', name='Harvey Specter', email='harvey@student.edu', password=make_password('student123'))

        # Some Follows
        Follow.objects.all().delete()
        Follow.objects.create(follower=s1, following=s2)
        Follow.objects.create(follower=s1, following=s3)
        Follow.objects.create(follower=s2, following=s1)
        Follow.objects.create(follower=s3, following=s4)
        Follow.objects.create(follower=s4, following=s1)

        # Posts
        Post.objects.all().delete()
        # Admin pinned post
        Post.objects.create(
            content='Welcome to UniBuzz! Please follow the community guidelines.',
            author_role='admin',
            author_id=admin.id,
            is_pinned=True,
            pin_expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Teacher posts
        Post.objects.create(content='The upcoming CS midterm has been postponed to next week.', author_role='teacher', author_id=t1.id)
        Post.objects.create(content='Office hours are cancelled for today.', author_role='teacher', author_id=t2.id)
        
        # Student posts
        Post.objects.create(content='Anyone want to study together for the Data Structures exam?', author_role='student', author_id=s1.id)
        Post.objects.create(content='Campus cafeteria food is getting better!', author_role='student', author_id=s2.id)

        self.stdout.write(self.style.SUCCESS("Successfully seeded data!"))
