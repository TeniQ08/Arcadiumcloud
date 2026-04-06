from django.core.management.base import BaseCommand

from game_sessions.services import mark_expired_sessions


class Command(BaseCommand):
    help = "Mark expired active sessions and queue deactivate_station on devices."

    def handle(self, *args, **options):
        n = mark_expired_sessions()
        self.stdout.write(self.style.SUCCESS(f"Marked {n} session(s) expired."))
