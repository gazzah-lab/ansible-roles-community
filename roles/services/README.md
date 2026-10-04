# gazzah.community.services

`services_list` is a list of maps with name, optional state (default started)
and optional enabled. Omit enabled for static units such as qemu-guest-agent.
Only declared services are managed; an empty list performs no operation.
Packages must already exist before starting their services.
