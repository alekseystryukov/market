from io import StringIO
from django.core.management import call_command


def get_migrations_info():
    # run 'show migrations'
    buf = StringIO()
    call_command("showmigrations", stdout=buf)
    output = buf.getvalue().replace("\x1b[1m", "").replace("\x1b[0m", "").replace("\x1b[31;1m", "")  # rm special chars
    # parse result
    migration_by_app = {}
    app_name = None
    for line in output.split("\n"):
        line = line.strip()
        if line:
            if line.startswith("["):
                migration_by_app[app_name].append({
                    "name": line[4:],
                    "applied": line.startswith("[X]"),
                })
            elif not line.startswith("("):  # (no migrations)
                app_name = line
                migration_by_app[app_name] = []
    return migration_by_app


def get_latest_applied(ms):
    result = {}
    for app_name, v in ms.items():
        for m in reversed(v):
            if m["applied"]:
                result[app_name] = m["name"]
                break
    return result
