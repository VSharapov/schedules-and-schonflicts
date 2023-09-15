#!/bin/bash

# Minimalist systemd service file generator
# For a fully featured tool, visit: https://github.com/NunuM/my-systemd-service-file-generator
# Official systemd service documentation: https://www.freedesktop.org/software/systemd/man/systemd.service.html

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <shortname> <execstart> [workingdir=\$(pwd) [description=\"${1:-"<shortname>"} service\" [restart=always [user=\$(whoami) [wantedby=multi-user.target]]]]]" >&2
    echo "Reminder: Root permissions are required and execstart probably needs quotes." >&2
    echo "Example that uses realpath to disambiguate execstart:" >&2
    echo "\`$0 myservice \"\$(realpath ./venv/bin/python) \$(realpath ./my-script.py)\"\`" >&2
    exit 1
fi

SHORTNAME=$1
EXECSTART=$2
WORKINGDIR=${3:-$(pwd)}
DESCRIPTION=${4:-"$SHORTNAME service"}
RESTART=${5:-"always"}
USER=${6:-$(whoami)}
WANTEDBY=${7:-"multi-user.target"}
SERVICE_FILE="/etc/systemd/system/${SHORTNAME}.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "Error: $SERVICE_FILE already exists." >&2
    exit 1
fi

if [ ! -w "/etc/systemd/system/" ]; then
    echo "Error: You do not have write permission to /etc/systemd/system/. Try running with sudo." >&2
    exit 1
fi

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=$DESCRIPTION

[Service]
ExecStart=$EXECSTART
WorkingDirectory=$WORKINGDIR
Restart=$RESTART
User=$USER

[Install]
WantedBy=$WANTEDBY
EOF

echo "Generated $SERVICE_FILE"
echo "---"
cat "$SERVICE_FILE"
echo "---"

echo "To manage the service, use:"
echo "sudo systemctl (start|stop|enable|disable|restart) ${SHORTNAME}.service"
