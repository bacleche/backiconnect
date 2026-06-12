from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid
from apps.courses.models import Course
from apps.users.models import User

class Certificate(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')


    file           = models.FileField(upload_to='certificates/pdfs/', blank=True, null=True)
    issued_at  = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'certificates'

    def __str__(self):
        return f"Certificat - {self.user.get_full_name()} - {self.course.title}"