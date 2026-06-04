from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid


from apps.users.models import User



class Course(models.Model):
    LEVEL_BEGINNER = 'beginner'
    LEVEL_INTERMEDIATE = 'intermediate'
    LEVEL_ADVANCED = 'advanced'

    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, 'Débutant'),
        (LEVEL_INTERMEDIATE, 'Intermédiaire'),
        (LEVEL_ADVANCED, 'Avancé'),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title         = models.CharField(max_length=255)
    slug          = models.SlugField(unique=True)
    description   = models.TextField()
    thumbnail     = models.ImageField(upload_to='courses/', blank=True, null=True)

    teacher       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')

    price         = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    level         = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    is_published  = models.BooleanField(default=False)

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    
    
class Section(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course    = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title     = models.CharField(max_length=255)
    order     = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        
        
class Lesson(models.Model):
    VIDEO = 'video'
    ARTICLE = 'article'

    LESSON_TYPE = [
        (VIDEO, 'Vidéo'),
        (ARTICLE, 'Article'),
    ]

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section   = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title     = models.CharField(max_length=255)
    content   = models.TextField(blank=True)
    video_url = models.URLField(blank=True)

    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE)
    duration    = models.PositiveIntegerField(help_text="Durée en secondes", default=0)
    order       = models.PositiveIntegerField(default=0)

    is_preview  = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        
        
        
class Enrollment(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course    = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress    = models.FloatField(default=0)  # %

    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')
        
        
class Review(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    course  = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')

    rating  = models.IntegerField()
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
class Payment(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    course  = models.ForeignKey(Course, on_delete=models.CASCADE)

    amount  = models.DecimalField(max_digits=10, decimal_places=2)
    status  = models.CharField(max_length=20, default='pending')

    transaction_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)