from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users import views

router = DefaultRouter()


urlpatterns = [


    # ─── Courses ───────────────────
    path('courses/', views.CourseViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('courses/<uuid:pk>/', views.CourseViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })),

    # ─── Sections ───────────────────
    path('sections/', views.SectionViewSet.as_view({
        'post': 'create'
    })),
    path('sections/<uuid:pk>/', views.SectionViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    })),

    # ─── Lessons ───────────────────
    path('lessons/', views.LessonViewSet.as_view({
        'post': 'create'
    })),
    path('lessons/<uuid:pk>/', views.LessonViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    })),

    # ─── Enrollment ───────────────────
    path('enrollments/', views.EnrollmentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),

    # ─── Reviews ───────────────────
    path('reviews/', views.ReviewViewSet.as_view({
        'post': 'create'
    })),
    path('reviews/<int:pk>/', views.ReviewViewSet.as_view({
        'delete': 'destroy'
    })),

    # ─── Payments ───────────────────
    path('payments/', views.PaymentViewSet.as_view({
        'post': 'create'
    })),

    # ─── Certificates ───────────────────
    path('certificates/', views.CertificateViewSet.as_view({
        'get': 'list'
    })),


    path('', include(router.urls)),

     # ─── OTP ─────────────────────────────
    path('otp/send/', views.OTPViewSet.as_view({'post': 'send_otp'}), name='send-otp'),
    path('otp/verify/', views.OTPViewSet.as_view({'post': 'verify_otp'}), name='verify-otp'),

    # ─── Conversations ───────────────────
    path('conversations/', views.ConversationViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='conversation-list'),

    path('conversations/<uuid:pk>/', views.ConversationViewSet.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    }), name='conversation-detail'),

    # ─── Messages ────────────────────────
    path('messages/', views.MessageViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='message-list'),

    path('messages/<uuid:pk>/', views.MessageViewSet.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    }), name='message-detail'),

    path('messages/by-conversation/', views.MessageViewSet.as_view({
        'get': 'by_conversation'
    }), name='messages-by-conversation'),
    
    path('me/', views.MeView.as_view(), name='user-me'),
    path('me/password/', views.ChangePasswordView.as_view(), name='user-change-password'),

    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/<uuid:pk>/', views.TeacherDetailView.as_view(), name='teacher-detail'),

    path('admin/', views.AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/<uuid:pk>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/<uuid:pk>/verify-teacher/', views.verify_teacher, name='admin-verify-teacher'),
    path('admin/<uuid:pk>/toggle-status/', views.toggle_user_status, name='admin-toggle-status'),
    path('admin/stats/', views.admin_stats, name='admin-user-stats'),
]