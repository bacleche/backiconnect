from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, StudentProfile, TeacherProfile , OTP , Conversation, Message 
from apps.courses.models import Course, Enrollment, Lesson, Payment, Review, Section
from apps.certificates.models import Certificate
from django.utils import timezone
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings

# ─── Token personnalisé ───────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email']      = user.email
        token['full_name']  = user.get_full_name()
        token['role']       = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id':        str(self.user.id),
            'email':     self.user.email,
            'full_name': self.user.get_full_name(),
            'role':      self.user.role,
            'avatar':    self.user.avatar.url if self.user.avatar else None,
        }
        return data


# ─── Inscription ──────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    role      = serializers.ChoiceField(choices=[('student', 'Étudiant'), ('teacher', 'Formateur')])

    class Meta:
        model  = User
        fields = ['email', 'first_name', 'last_name', 'role', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        # Créer le profil étendu selon le rôle
        if user.role == User.STUDENT:
            StudentProfile.objects.create(user=user)
        elif user.role == User.TEACHER:
            TeacherProfile.objects.create(user=user)
        return user


# ─── Profils ──────────────────────────────────────────────
class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StudentProfile
        fields = ['level', 'total_points', 'streak_days', 'last_activity']


class TeacherProfileSerializer(serializers.ModelSerializer):
    expertise = serializers.CharField(source='user.expertise', read_only=True)

    class Meta:
        model  = TeacherProfile
        fields = [
            'total_students',
            'total_courses',
            'average_rating',
            'total_revenue',
            'revenue_share_pct',
            'expertise',
        ]
# ─── Utilisateur (lecture) ────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    full_name       = serializers.CharField(source='get_full_name', read_only=True)
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'bio', 'phone', 'expertise',
            'is_verified_teacher', 'date_joined',
            'student_profile', 'teacher_profile',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'is_verified_teacher']


# ─── Mise à jour du profil ────────────────────────────────
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'bio', 'phone', 'avatar', 'expertise']


# ─── Changement de mot de passe ───────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# ─── Formateur public (pour les étudiants) ────────────────
class PublicTeacherSerializer(serializers.ModelSerializer):
    full_name       = serializers.CharField(source='get_full_name', read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'full_name', 'avatar', 'bio', 'expertise',
                  'is_verified_teacher', 'teacher_profile']


# ─── Liste admin ──────────────────────────────────────────
class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'full_name', 'role', 'is_active',
                  'is_verified_teacher', 'date_joined']
        
        

class OTPCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['id', 'user', 'code', 'expires_at']
        read_only_fields = ['code', 'expires_at']

    def create(self, validated_data):
        user = validated_data['user']
        code = OTP.generate_code()
        expires_at = timezone.now() + timedelta(minutes=5)

        otp = OTP.objects.create(user=user, code=code, expires_at=expires_at)

        send_mail(
            subject='Votre code de vérification iConnect',
            message=f'Votre code OTP est : {code}\nIl expire dans 5 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return otp
    
    
class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code  = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get('email')
        code  = data.get('code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")

        otp = OTP.objects.filter(user=user, code=code, is_used=False).first()

        if not otp:
            raise serializers.ValidationError("Code OTP invalide.")

        if not otp.is_valid():
            raise serializers.ValidationError("OTP expiré ou déjà utilisé.")

        data['user'] = user
        data['otp']  = otp
        return data
    
    



# ─── User simple (pour affichage) ───────────────────
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'avatar']


# ─── Message ───────────────────
class MessageSerializer(serializers.ModelSerializer):
    sender = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'content',
            'file',
            'message_type',
            'is_read',
            'created_at'
        ]
        read_only_fields = ['sender', 'is_read', 'created_at']


# ─── Conversation ───────────────────
class ConversationSerializer(serializers.ModelSerializer):
    participants = SimpleUserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants',
            'last_message',
            'created_at',
            'updated_at'
        ]

    def get_last_message(self, obj):
        message = obj.messages.last()
        return MessageSerializer(message).data if message else None


# ─── Création conversation ───────────────────
class ConversationCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()

    def validate(self, data):
        request_user = self.context['request'].user
        other_user_id = data['user_id']

        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable")

        roles = {request_user.role, other_user.role}

        if roles != {User.STUDENT, User.TEACHER}:
            raise serializers.ValidationError("Conversation autorisée uniquement entre étudiant et formateur")

        data['other_user'] = other_user
        return data
    
    
    


# ─── User simple ───────────────────
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


# ─── Lesson ───────────────────
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'


# ─── Section ───────────────────
class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = '__all__'


# ─── Course ───────────────────
class CourseSerializer(serializers.ModelSerializer):
    teacher = SimpleUserSerializer(read_only=True)
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


# ─── Enrollment ───────────────────
class EnrollmentSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = '__all__'


# ─── Review ───────────────────
class ReviewSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = '__all__'


# ─── Payment ───────────────────
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


# ─── Certificate ───────────────────
class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'