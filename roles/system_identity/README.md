# gazzah.community.system_identity

`system_identity_hostname` defaults to inventory_hostname. Manage hostname and
its 127.0.1.1 entry with `system_identity_manage_hostname` and
`system_identity_manage_hosts`. Other hosts entries are preserved.
Set `system_identity_timezone` to an IANA timezone; null leaves it unchanged.
No network configuration is modified.
