# Debian VM baseline

Debian 13 VM configuration, without account profiles or network changes.
Install common packages (SSH, chrony, rsyslog, tzdata, ca-certificates) before
running system sections. `unattended` installs its own update tools.

Select `debian_baseline_sections` from apt, identity, shell, ssh, services,
unattended; matching tags are available. Debian repositories use deb822 and
HTTPS; third-party source files are preserved. APT full-upgrade and reboot are
not implicit. Security updates use the `trixie-security` codename and do not
reboot automatically. The QEMU agent is only started (its unit is static).

SSH defaults to keys only, root by key. Override with
`debian_baseline_password_authentication` and `debian_baseline_permit_root_login`.
The `00-gazzah.conf` snippet precedes cloud-init and former `10-local.conf` is
removed. Configuration is validated before a handler reloads SSH.

Hostname, timezone and the machine's display role are inventory variables:
`debian_baseline_hostname`, `debian_baseline_timezone`, `debian_baseline_node_role`.
No IP, DNS, route or interface is changed by this role. Proxmox/cloud-init owns
first-boot networking. Do not apply the VM baseline to Proxmox hosts or routers.

For isolated container tests only, set `debian_baseline_manage_services: false`
to avoid systemd and hostname operations; file/configuration tasks still run.

When canonical repositories change, the APT section refreshes package indexes
before later installations. Check mode does not fetch indexes; run the APT
section normally before previewing package installation on a fresh machine.
`tests/apt-cache.yml` checks installation without an additional cache refresh;
run it only in a disposable Debian 13 container with CA certificates installed.
