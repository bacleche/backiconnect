from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid
from apps.courses.models import Course
from apps.users.models import User

class LiveSession(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_sessions')
    teacher     = models.ForeignKey(User, on_delete=models.CASCADE)

    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    start_time  = models.DateTimeField()
    end_time    = models.DateTimeField()

    meeting_url = models.URLField()
    is_active   = models.BooleanField(default=True)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'live_sessions'