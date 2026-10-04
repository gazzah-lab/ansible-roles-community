#!/bin/bash

# Seulement pour les shells interactifs.
case "$-" in
    *i*) ;;
    *) return 0 2>/dev/null || exit 0 ;;
esac

GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
BLUE="\e[34m"
RESET="\e[0m"

HOST="$(hostname)"
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
OS="$(grep '^PRETTY_NAME=' /etc/os-release | cut -d= -f2- | tr -d '"')"
KERNEL="$(uname -r)"
UPTIME="$(uptime -p | sed 's/^up //')"
LOAD="$(awk '{print $1", "$2", "$3}' /proc/loadavg)"
DATE="$(date '+%a %d %b %Y %H:%M:%S %Z')"

CPU="$(nproc)"

RAM_USED="$(free -m | awk '/^Mem:/ {print $3}')"
RAM_TOTAL="$(free -m | awk '/^Mem:/ {print $2}')"

DISK_USED_PCT="$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')"
DISK_USED="$(df -hP / | awk 'NR==2 {print $3}')"
DISK_TOTAL="$(df -hP / | awk 'NR==2 {print $2}')"

ROLE_FILE="/etc/node-role"

if [[ -s "$ROLE_FILE" ]]; then
    ROLE="$(cat "$ROLE_FILE")"
else
    ROLE="generic"
fi

if (( DISK_USED_PCT >= 90 )); then
    DISK_COLOR="$RED"
    DISK_STATUS="CRITICAL"
elif (( DISK_USED_PCT >= 75 )); then
    DISK_COLOR="$YELLOW"
    DISK_STATUS="WARNING"
else
    DISK_COLOR="$GREEN"
    DISK_STATUS="OK"
fi

echo
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e " 🖥  ${BLUE}${HOST}${RESET} (${ROLE})"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e " 🌐 IP        : ${IP:-non disponible}"
echo -e " 🧠 OS        : $OS"
echo -e " 🧩 Kernel    : $KERNEL"
echo -e " ⏱  Uptime    : $UPTIME"
echo -e " 📊 Load      : $LOAD"
echo -e " 🧮 CPU       : ${CPU} cores"
echo -e " 💾 RAM       : ${RAM_USED}MB / ${RAM_TOTAL}MB"
echo -e " 💽 Disk /    : ${DISK_USED}/${DISK_TOTAL}  ${DISK_COLOR}${DISK_USED_PCT}% (${DISK_STATUS})${RESET}"
echo -e " 📅 Date      : $DATE"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
