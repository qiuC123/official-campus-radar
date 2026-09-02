#!/usr/bin/env python
import os
import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "test":
        from campus_radar.environment import load_project_exa_key

        load_project_exa_key()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
