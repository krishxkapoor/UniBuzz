from django.db import models

class TeacherUser(models.Model):
    id = models.AutoField(primary_key=True)
    employee_id = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='teachers/profile_pics/', blank=True, null=True)
    department = models.CharField(max_length=100)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
