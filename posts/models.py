from django.db import models
from django.utils import timezone

ROLE_CHOICES = [('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')]

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    author_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    author_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)
    pin_expires_at = models.DateTimeField(blank=True, null=True)

    def is_pin_active(self):
        if self.is_pinned and self.pin_expires_at:
            return timezone.now() < self.pin_expires_at
        return False

REACTION_CHOICES = [
    ('like', 'Like'),
    ('celebrate', 'Celebrate'),
    ('insightful', 'Insightful'),
    ('funny', 'Funny')
]

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    liker_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    liker_id = models.PositiveIntegerField()
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'liker_role', 'liker_id')

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    author_id = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

REPORT_REASON_CHOICES = [
    ('spam', 'Spam'),
    ('harassment', 'Harassment'),
    ('misinformation', 'Misinformation'),
    ('inappropriate', 'Inappropriate Content'),
    ('other', 'Other'),
]

REPORT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('resolved', 'Resolved'),
    ('dismissed', 'Dismissed'),
]

class Report(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reporter_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    reporter_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=REPORT_REASON_CHOICES, default='other')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=REPORT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'reporter_role', 'reporter_id')

class SavedPost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    saver_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    saver_id = models.PositiveIntegerField()
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'saver_role', 'saver_id')

class GenericFollow(models.Model):
    follower_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    follower_id = models.PositiveIntegerField()
    following_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    following_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower_role', 'follower_id', 'following_role', 'following_id')
