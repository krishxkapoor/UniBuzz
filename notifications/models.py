from django.db import models

class Notification(models.Model):
    recipient_role = models.CharField(max_length=10)
    recipient_id = models.PositiveIntegerField()
    notif_type = models.CharField(max_length=20) # 'like', 'comment', 'follow', 'pin'
    actor_role = models.CharField(max_length=10)
    actor_id = models.PositiveIntegerField()
    post = models.ForeignKey('posts.Post', null=True, blank=True, on_delete=models.SET_NULL)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
