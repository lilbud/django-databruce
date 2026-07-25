# CHANGE THIS IMPORT: Import from staticfiles instead of core django
import sys

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)


class Command(RunserverCommand):
    help = "Starts a lightweight web server with a selectable default database and static files."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--db",
            action="store",
            dest="target_db",
            default=None,
            help="Specify the database alias to map to default",
        )

    def handle(self, *args, **options):
        target_db = options.get("target_db")

        if target_db:
            if target_db not in settings.DATABASES:
                self.stderr.write(
                    f"Error: Database '{target_db}' is not defined in settings.DATABASES."
                )
                sys.exit(1)

            self.stdout.write(f"Switching default database to profile: '{target_db}'")
            settings.DATABASES["default"] = settings.DATABASES[target_db]

        super().handle(*args, **options)
