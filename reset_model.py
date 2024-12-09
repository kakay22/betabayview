from django.core.management.base import BaseCommand
from ADMIN.models import Message
from django.db import connection

class Command(BaseCommand):
    help = 'Resets the YourModel table and IDs'

    def handle(self, *args, **kwargs):
        Message.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute("ALTER SEQUENCE ADMIN_Message_id_seq RESTART WITH 1;")
        self.stdout.write(self.style.SUCCESS('Successfully reset YourModel table.'))