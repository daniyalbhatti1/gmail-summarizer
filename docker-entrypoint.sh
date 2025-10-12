#!/bin/bash
set -e

echo "=================================================="
echo "Gmail Digest Docker Container"
echo "=================================================="
echo "Timezone: ${TZ:-America/New_York}"
echo "Starting at: $(date)"
echo "=================================================="

# Set timezone
if [ -n "$TZ" ]; then
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
    echo $TZ > /etc/timezone
fi

# Create crontab if it doesn't exist
CRON_FILE=/etc/cron.d/gmail-digest

# Convert scheduled times to cron format
# Default: 09:00 and 13:00 in container's timezone
cat > $CRON_FILE << EOF
# Gmail Digest Schedule
# Run at 09:00 and 13:00 in ${TZ:-America/New_York}

0 9 * * * root cd /app && /usr/local/bin/python -m src.main >> /app/logs/digest.log 2>&1
0 13 * * * root cd /app && /usr/local/bin/python -m src.main >> /app/logs/digest.log 2>&1

# Empty line required at end of crontab
EOF

chmod 0644 $CRON_FILE
crontab $CRON_FILE

echo "Crontab configured:"
cat $CRON_FILE
echo "=================================================="

# If running cron, start it in foreground
if [ "$1" = "cron" ]; then
    echo "Starting cron daemon..."
    cron -f
else
    # Otherwise, run the provided command
    exec "$@"
fi

