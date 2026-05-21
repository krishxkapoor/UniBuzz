from django.db import models

class StudentUser(models.Model):
    id = models.AutoField(primary_key=True)
    roll_number = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='students/profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Follow(models.Model):
    follower = models.ForeignKey(StudentUser, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(StudentUser, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.name} follows {self.following.name}"
