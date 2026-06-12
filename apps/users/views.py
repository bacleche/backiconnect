from rest_framework import generics, status, permissions , viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from iconnect_Backend.permissions import IsAdmin, IsAdminOrTeacher
from apps.certificates.models import Certificate
from apps.courses.models import Course, Enrollment, Lesson, Lesson, Payment, Payment, Review, Section, Section
from .models import *
from .serializers import (
    CustomTokenObtainPairSerializer,
    CertificateSerializer,
    OTPVerifySerializer,
    RegisterSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
    PublicTeacherSerializer,
    AdminUserSerializer,
    OTPCreateSerializer  ,
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    CourseSerializer,
    MessageSerializer,
    SectionSerializer,
    LessonSerializer,
    EnrollmentSerializer,
    PaymentSerializer,
    ReviewSerializer
)

User = get_user_model()


# ─── Authentification ─────────────────────────────────────

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()
        OTP.objects.filter(user=user, is_used=False, expires_at__lt=timezone.now()).delete()

        if user and user.check_password(password):
            # Dans LoginView.post, avant de créer un nouvel OTP :
            otp_serializer = OTPCreateSerializer(data={'user': user.id})
            if otp_serializer.is_valid():
                otp_serializer.save()
                return Response({
                    "message": "OTP requis",
                    "requires_otp": True,
                    "email": user.email
                }, status=status.HTTP_200_OK)
        
        return Response({"error": "Identifiants invalides"}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouvel utilisateur (étudiant ou formateur)."""
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("--- ERREURS DE VALIDATION ---")
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()  # ← une seule fois
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Inscription réussie.',
            'user': {
                'id':        str(user.id),
                'email':     user.email,
                'full_name': user.get_full_name(),
                'role':      user.role,
            },
            'tokens': {
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)





class LogoutView(APIView):
    """Déconnexion – blackliste le refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)


# ─── Profil utilisateur ───────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    """Récupérer et mettre à jour son propre profil."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateProfileSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Changer son mot de passe."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Mot de passe modifié avec succès.'})


# ─── Formateurs publics ───────────────────────────────────

class TeacherListView(generics.ListAPIView):
    """Liste publique des formateurs vérifiés."""
    serializer_class   = PublicTeacherSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [SearchFilter, OrderingFilter]
    search_fields      = ['first_name', 'last_name', 'expertise', 'bio']
    ordering_fields    = ['date_joined']

    def get_queryset(self):
        return User.objects.filter(
            role=User.TEACHER,
            is_verified_teacher=True,
            is_active=True
        ).select_related('teacher_profile')


class TeacherDetailView(generics.RetrieveAPIView):
    """Détail public d'un formateur."""
    serializer_class   = PublicTeacherSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return User.objects.filter(role=User.TEACHER, is_active=True)


# ─── Administration ───────────────────────────────────────

class AdminUserListView(generics.ListAPIView):
    """[Admin] Liste de tous les utilisateurs."""
    serializer_class   = AdminUserSerializer
    permission_classes = [IsAdmin]
    queryset           = User.objects.all().order_by('-date_joined')
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['role', 'is_active', 'is_verified_teacher']
    search_fields      = ['email', 'first_name', 'last_name']
    ordering_fields    = ['date_joined', 'email']


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """[Admin] Détail, modification et suppression d'un utilisateur."""
    serializer_class   = AdminUserSerializer
    permission_classes = [IsAdmin]
    queryset           = User.objects.all()


@api_view(['POST'])
@permission_classes([IsAdmin])
def verify_teacher(request, pk):
    """[Admin] Valider un formateur."""
    try:
        user = User.objects.get(pk=pk, role=User.TEACHER)
        user.is_verified_teacher = True
        user.save()
        return Response({'message': f'{user.get_full_name()} est maintenant formateur vérifié.'})
    except User.DoesNotExist:
        return Response({'error': 'Formateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdmin])
def toggle_user_status(request, pk):
    """[Admin] Activer / suspendre un compte."""
    try:
        user = User.objects.get(pk=pk)
        user.is_active = not user.is_active
        user.save()
        state = 'activé' if user.is_active else 'suspendu'
        return Response({'message': f'Compte {state}.', 'is_active': user.is_active})
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_stats(request):
    """[Admin] Statistiques globales des utilisateurs."""
    from django.db.models import Count
    stats = User.objects.aggregate(
        total=Count('id'),
        students=Count('id', filter=__import__('django.db.models', fromlist=['Q']).Q(role='student')),
        teachers=Count('id', filter=__import__('django.db.models', fromlist=['Q']).Q(role='teacher')),
        admins=Count('id',   filter=__import__('django.db.models', fromlist=['Q']).Q(role='admin')),
    )
    return Response(stats)







class OTPViewSet(viewsets.ViewSet):

    permission_classes = [permissions.AllowAny]  # ← ajoute cette ligne

    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        serializer = OTPCreateSerializer(data=request.data)

        if serializer.is_valid():
            otp = serializer.save()
            return Response({
                "message": "OTP envoyé avec succès",
                "otp_id": otp.id  # à retirer en prod
            }, status=status.HTTP_201_CREATED)

        return Response({"message": "OTP envoyé à votre adresse email."}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = OTPVerifySerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp = serializer.validated_data['otp']
            otp.is_used = True
            otp.save()

            # GÉNÉRATION DES TOKENS ICI UNIQUEMENT
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Authentification réussie",
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


    # views.py
class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Utilisateur introuvable."}, status=404)
        
        OTP.objects.filter(user=user, is_used=False).delete()
        otp_serializer = OTPCreateSerializer(data={'user': user.id})
        if otp_serializer.is_valid():
            otp_serializer.save()
        return Response({"message": "OTP renvoyé."})


# ─── Conversation ViewSet ───────────────────
class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related('participants', 'messages')

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        other_user = serializer.validated_data['other_user']

        # 🔍 Vérifie si conversation existe déjà
        conversation = Conversation.objects.filter(
            participants=user
        ).filter(
            participants=other_user
        ).first()

        if conversation:
            return Response(ConversationSerializer(conversation).data)

        # ✅ Création
        conversation = Conversation.objects.create()
        conversation.participants.set([user, other_user])

        return Response(ConversationSerializer(conversation).data, status=201)


# ─── Message ViewSet ───────────────────
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related('sender', 'conversation')

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']

        # 🔐 Sécurité
        if self.request.user not in conversation.participants.all():
            raise PermissionError("Accès refusé à cette conversation")

        serializer.save(sender=self.request.user)

    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        conversation_id = request.query_params.get('conversation_id')

        messages = self.get_queryset().filter(conversation_id=conversation_id)

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    
    


# ─── Course ───────────────────
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related('teacher')
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


# ─── Section ───────────────────
class SectionViewSet(viewsets.ModelViewSet):
    queryset =  Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]


# ─── Lesson ───────────────────
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]


# ─── Enrollment ───────────────────
class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ─── Review ───────────────────
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ─── Payment ───────────────────
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


# ─── Certificate ───────────────────
class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)