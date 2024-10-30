from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a new user with a default password'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new user')
        parser.add_argument('email', type=str, help='Email address for the new user')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        password = 'default'  # Default password

        User = get_user_model()

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f"User '{username}' already exists"))
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"User '{username}' created with password 'default'"))
