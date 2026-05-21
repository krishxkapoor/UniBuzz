from django.db import models

class DirectMessage(models.Model):
    sender_role = models.CharField(max_length=10)
    sender_id = models.PositiveIntegerField()
    receiver_role = models.CharField(max_length=10)
    receiver_id = models.PositiveIntegerField()
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

class Group(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey('students.StudentUser', on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField('students.StudentUser', related_name='groups')
    group_pic = models.ImageField(upload_to='groups/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('students.StudentUser', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
