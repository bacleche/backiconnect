from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, StudentProfile, TeacherProfile


class StudentProfileInline(admin.StackedInline):
    model  = StudentProfile
    extra  = 0
    fields = ['level', 'total_points', 'streak_days', 'last_activity']


class TeacherProfileInline(admin.StackedInline):
    model  = TeacherProfile
    extra  = 0
    fields = ['total_students', 'total_courses', 'average_rating',
              'total_revenue', 'revenue_share_pct', 'bank_account']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['avatar_tag', 'email', 'get_full_name', 'role_badge',
                     'is_active', 'is_verified_teacher', 'date_joined']
    list_filter   = ['role', 'is_active', 'is_verified_teacher', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering      = ['-date_joined']
    list_per_page = 30

    fieldsets = (
        ('Identifiants', {'fields': ('email', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'avatar', 'bio', 'phone', 'expertise')
        }),
        ('Rôle & statut', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified_teacher')
        }),
        ('Permissions', {'fields': ('groups', 'user_permissions'), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == User.STUDENT:
            return [StudentProfileInline]
        if obj.role == User.TEACHER:
            return [TeacherProfileInline]
        return []

    @admin.display(description='Avatar')
    def avatar_tag(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="36" height="36" style="border-radius:50%;object-fit:cover"/>', obj.avatar.url)
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#4f46e5,#06b6d4);'
            'display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px">{}</div>',
            initials
        )

    @admin.display(description='Rôle')
    def role_badge(self, obj):
        colors = {
            'student': ('#ede9fe', '#4f46e5'),
            'teacher': ('#cffafe', '#0e7490'),
            'admin':   ('#fee2e2', '#ef4444'),
        }
        bg, fg = colors.get(obj.role, ('#f3f4f6', '#6b7280'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:999px;'
            'font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.get_role_display()
        )

    actions = ['activate_users', 'suspend_users', 'verify_teachers']

    @admin.action(description='✅ Activer les comptes sélectionnés')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Suspendre les comptes sélectionnés')
    def suspend_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='🎓 Valider les formateurs sélectionnés')
    def verify_teachers(self, request, queryset):
        queryset.filter(role=User.TEACHER).update(is_verified_teacher=True)