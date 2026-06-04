from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid
from django.utils import timezone
import random
import string

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ADMIN)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN   = 'admin'

    ROLE_CHOICES = [
        (STUDENT, 'Étudiant'),
        (TEACHER, 'Formateur'),
        (ADMIN,   'Administrateur'),
    ]

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email         = models.EmailField(unique=True)
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    role          = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    avatar        = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio           = models.TextField(blank=True)
    phone         = models.CharField(max_length=20, blank=True)

    # Formateurs uniquement
    expertise     = models.CharField(max_length=255, blank=True)
    is_verified_teacher = models.BooleanField(default=False)

    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    date_joined   = models.DateTimeField(auto_now_add=True)
    last_login    = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.TEACHER

    @property
    def is_student(self):
        return self.role == self.STUDENT


class StudentProfile(models.Model):
    """Profil étendu étudiant."""
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    level           = models.CharField(max_length=50, blank=True)
    total_points    = models.PositiveIntegerField(default=0)
    streak_days     = models.PositiveIntegerField(default=0)
    last_activity   = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'student_profiles'
        verbose_name = 'Profil étudiant'

    def __str__(self):
        return f"Profil – {self.user.get_full_name()}"


class TeacherProfile(models.Model):
    """Profil étendu formateur."""
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    total_students    = models.PositiveIntegerField(default=0)
    total_courses     = models.PositiveIntegerField(default=0)
    average_rating    = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_revenue     = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bank_account      = models.CharField(max_length=100, blank=True)
    revenue_share_pct = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)

    class Meta:
        db_table = 'teacher_profiles'
        verbose_name = 'Profil formateur'

    def __str__(self):
        return f"Formateur – {self.user.get_full_name()}"
    
    





class OTP(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code        = models.CharField(max_length=6)
    created_at  = models.DateTimeField(auto_now_add=True)
    expires_at  = models.DateTimeField()
    is_used     = models.BooleanField(default=False)

    class Meta:
        db_table = 'otps'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP {self.code} - {self.user.email}"

    @staticmethod
    def generate_code():
        """Génère un OTP à 6 chiffres."""
        return ''.join(random.choices(string.digits, k=6))

    def is_valid(self):
        """Vérifie si OTP est valide."""
        return not self.is_used and self.expires_at > timezone.now()
    


# ─── Conversation ───────────────────────────────────
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id}"

    def clean(self):
        users = self.participants.all()

        if users.count() != 2:
            raise ValueError("Une conversation doit avoir exactement 2 participants.")

        roles = set(user.role for user in users)

        if roles != {User.STUDENT, User.TEACHER}:
            raise ValueError("Conversation uniquement entre étudiant et formateur")


# ─── Message ───────────────────────────────────
class Message(models.Model):

    TEXT = 'text'
    IMAGE = 'image'
    FILE = 'file'

    MESSAGE_TYPE_CHOICES = [
        (TEXT, 'Texte'),
        (IMAGE, 'Image'),
        (FILE, 'Fichier'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')

    content      = models.TextField(blank=True)
    file         = models.FileField(upload_to='messages/', blank=True, null=True)

    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default=TEXT)

    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.sender.email} -> {self.conversation.id}"
  
    
    
    
    
    
    
    
#     ok maintenant je veux creer mon app next js , donne moi la procedure  le nom c'est  iconnect-welearn 

# et tu me donnes toute la structure l'app sera combiné avec la partie site qui donnera acces au formulaire de connexion , register et laissera acces aux differents dashboard (admin , formateur , etudiant) 