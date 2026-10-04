# gazzah.community.apt_repositories

Manage only named deb822 source files and explicitly requested APT options.
Each `apt_repositories_sources` entry defines name, uris, suites, components,
optional types, architectures, signed_by and state (present/absent).
No infrastructure address, release or component is hardcoded.
Other sources are preserved. `apt_repositories_manage_legacy_file: true`
explicitly clears the legacy sources.list; default false.
`apt_repositories_options` is a map of APT configuration keys and values.
APT indexes are refreshed on source changes before installing packages.
Check mode cannot populate missing indexes.
