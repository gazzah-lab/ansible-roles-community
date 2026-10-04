#!/bin/sh

# Uniquement pour Bash interactif.
[ -n "${BASH_VERSION:-}" ] || return 0 2>/dev/null || exit 0

case "$-" in
    *i*) ;;
    *) return 0 2>/dev/null || exit 0 ;;
esac

PROMPT_COMMAND='
if [ "$(id -u)" -eq 0 ]; then
    PS1="\[\e]0;\u@\h: \w\a\][\[\e[31m\]\t\[\e[m\]] \u@\[\e[36m\]\h\[\e[m\]:\w \[\e[31m\]\\$\[\e[m\] "
else
    PS1="\[\e]0;\u@\h: \w\a\][\[\e[32m\]\t\[\e[m\]] \u@\[\e[36m\]\h\[\e[m\]:\w \[\e[32m\]\\$\[\e[m\] "
fi
'
