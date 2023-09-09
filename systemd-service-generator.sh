#!/bin/bash

# Minimalist systemd service file generator
# For a fully featured tool, visit: https://github.com/NunuM/my-systemd-service-file-generator
# Official systemd service documentation: https://www.freedesktop.org/software/systemd/man/systemd.service.html

# Check if the required arguments are present
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <shortname> <execstart> [description [restart [user [wantedby]]]]" >&2
    echo "Example that uses realpath to disambiguate execstart:" >&2
    echo "\`$0 myservice \"\$(realpath ./venv/bin/python) \$(realpath ./my-script.py)\"\`" >&2
    exit 1
fi

# Assign arguments to variables
SHORTNAME=$1
EXECSTART=$2
DESCRIPTION=${3:-"A systemd service"}
RESTART=${4:-"always"}
USER=${5:-$(whoami)}
WANTEDBY=${6:-"multi-user.target"}

# Check if the service file already exists
if [ -f "/etc/systemd/system/${SHORTNAME}.service" ]; then
    echo "Error: Service file /etc/systemd/system/${SHORTNAME}.service already exists." >&2
    exit 1
fi

# Generate the service file content
cat <<EOF > "/etc/systemd/system/${SHORTNAME}.service"
[Unit]
Description=$DESCRIPTION

[Service]
ExecStart=$EXECSTART
Restart=$RESTART
User=$USER

[Install]
WantedBy=$WANTEDBY
EOF

echo "Generated ${SHORTNAME}.service"

# Quick common usage summary
echo "To manage the service, use:"
echo "sudo systemctl (start|stop|enable|disable|restart) ${SHORTNAME}.service"
