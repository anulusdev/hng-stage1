from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid6


class UserManager(BaseUserManager):
    """
    Custom manager because our User has no username/password —
    only GitHub identity. Django requires a manager that defines
    create_user and create_superuser even if we don't use passwords.
    """

    def create_user(self, github_id, **extra_fields):
        if not github_id:
            raise ValueError('github_id is required')
        user = self.model(github_id=github_id, **extra_fields)
        # No password — authentication is entirely via GitHub OAuth
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, github_id, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(github_id, **extra_fields)


class User(AbstractBaseUser):
    """
    Custom User model that replaces Django's built-in User.

    Why AbstractBaseUser instead of AbstractUser?
    AbstractUser assumes username + password login.
    AbstractBaseUser gives us a blank slate — we define exactly
    what fields we need for GitHub OAuth authentication.

    Why do we need to replace Django's User at all?
    SimpleJWT generates tokens using the User model's primary key.
    Our User needs UUID v7 as primary key and GitHub-specific fields.
    We cannot add these cleanly to Django's default User model.
    """

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('analyst', 'Analyst'),
    ]

    # UUID v7 primary key — consistent with Profile model
    id = models.UUIDField(
        primary_key=True,
        default=uuid6.uuid7,
        editable=False
    )

    # GitHub identity — this is our unique identifier, not email
    # because emails can change but GitHub numeric IDs never do
    github_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')

    # Role-based access control
    # Default is analyst — read only access
    # Admins must be manually promoted
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='analyst'
    )

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # AbstractBaseUser requires this — it's the field used for login
    # We use github_id as the unique login identifier
    USERNAME_FIELD = 'github_id'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"@{self.username} ({self.role})"

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff