#!/usr/bin/python
"""Plan and apply explicitly enabled Linux account identity migrations."""
from ansible.module_utils.basic import AnsibleModule
import grp
import os
import pwd
import shutil
import subprocess

DOCUMENTATION = r'''
---
module: accounts_migrate
short_description: Migrate declared account identities before account creation
options:
  users:
    type: list
    elements: dict
    required: true
  groups:
    type: list
    elements: dict
    default: []
  ownership_roots:
    type: list
    elements: path
    default: [/]
  excluded_paths:
    type: list
    elements: path
    default: [/proc, /sys, /dev, /run, /var/lib/docker, /var/lib/containerd]
  protected_user:
    type: str
    default: ''
author: gazzah-lab
'''
EXAMPLES = r'''
- name: Migrate account identities
  gazzah.community.accounts_migrate:
    users: [{name: sysmoudir, uid: 2000, group: sysmoudir, gid: 2000, home: /var/lib/sysmoudir}]
'''
RETURN = r'''
plan:
  description: Account changes without passwords or SSH keys
  type: list
  returned: always
'''


def plan_changes(users, groups, passwd, groupdb, protected_user):
    present = [u for u in users if u.get('state', 'present') == 'present']
    desired_groups = {g['name']: g['gid'] for g in groups if g.get('state', 'present') == 'present' and 'gid' in g}
    for u in present:
        if 'group' in u and 'gid' in u:
            if u['group'] in desired_groups and desired_groups[u['group']] != u['gid']:
                raise ValueError('Inconsistent primary group GID: ' + u['group'])
            desired_groups[u['group']] = u['gid']
    desired_users = {u['name']: u['uid'] for u in present if 'uid' in u}
    for desired, existing, attr in [(desired_users, passwd, 'pw_uid'), (desired_groups, groupdb, 'gr_gid')]:
        if len(set(desired.values())) != len(desired):
            raise ValueError('Duplicate desired identifiers')
        for name, ident in desired.items():
            if type(ident) is not int or ident < 0:
                raise ValueError('Invalid identifier for ' + name)
            for owner, entry in existing.items():
                if getattr(entry, attr) == ident and owner != name:
                    if owner not in desired or desired[owner] == ident:
                        raise ValueError('Identifier occupied by an unmanaged account/group: ' + owner)
    plan = []
    for name, gid in desired_groups.items():
        if name in groupdb and groupdb[name].gr_gid != gid:
            if name == 'root' or groupdb[name].gr_gid == 0 or gid == 0:
                raise ValueError('Root group migration forbidden')
            plan.append(dict(kind='gid', name=name, old=groupdb[name].gr_gid, new=gid))
    for u in present:
        name = u['name']
        if name not in passwd:
            continue
        entry = passwd[name]
        for kind, old, new in [('uid', entry.pw_uid, u.get('uid', entry.pw_uid)), ('home', entry.pw_dir, u.get('home', entry.pw_dir))]:
            if old == new:
                continue
            if name in ('root', protected_user) or entry.pw_uid == 0 or (kind == 'uid' and new == 0):
                raise ValueError('Migration forbidden for root or the connection account: ' + name)
            if kind == 'home':
                if not os.path.isabs(new) or new == '/' or os.path.lexists(new):
                    raise ValueError('Home destination must be absolute and absent: ' + name)
                if not os.path.isdir(old) or os.path.islink(old) or os.path.ismount(old):
                    raise ValueError('Home must be an existing directory, not a symlink or mount: ' + name)
            plan.append(dict(kind=kind, name=name, old=old, new=new))
    return plan


def main():
    module = AnsibleModule(argument_spec=dict(users=dict(type='list', elements='dict', required=True), groups=dict(type='list', elements='dict', default=[]), ownership_roots=dict(type='list', elements='path', default=['/']), excluded_paths=dict(type='list', elements='path', default=['/proc', '/sys', '/dev', '/run', '/var/lib/docker', '/var/lib/containerd']), protected_user=dict(type='str', default='')), supports_check_mode=True)
    plan = []
    mutated = False
    try:
        passwd = {u.pw_name: u for u in pwd.getpwall()}
        groupdb = {g.gr_name: g for g in grp.getgrall()}
        plan = plan_changes(module.params['users'], module.params['groups'], passwd, groupdb, module.params['protected_user'])
        roots = module.params['ownership_roots']
        if not roots or any(not os.path.isdir(r) or os.path.islink(r) for r in roots):
            raise ValueError('Ownership roots must be existing directories')
        moving = {p['name'] for p in plan if p['kind'] in ('uid', 'home')}
        moving_gids = {p['old'] for p in plan if p['kind'] == 'gid'}
        # Never kill sessions or services implicitly. Inspect all process credentials.
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            try:
                with open('/proc/' + pid + '/status', encoding='utf-8') as f:
                    fields = dict(line.split(':', 1) for line in f if ':' in line)
                uids = {int(x) for x in fields.get('Uid', '').split()}
                gids = {int(x) for x in (fields.get('Gid', '') + fields.get('Groups', '')).split()}
                if any(passwd[name].pw_uid in uids for name in moving) or moving_gids.intersection(gids):
                    raise ValueError('Active process prevents migration (PID ' + pid + '); stop the affected sessions/services first')
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
        if module.check_mode or not plan:
            module.exit_json(changed=bool(plan), plan=plan)

        def run(args):
            result = subprocess.run(args, capture_output=True, text=True, check=False)
            if result.returncode:
                raise RuntimeError('Command failed: ' + ' '.join(args) + ': ' + result.stderr.strip())

        def ownership(kind, old, new):
            # find -xdev avoids touching other mounted filesystems. Do not follow links.
            for root in roots:
                args = ['find', root, '-xdev']
                excluded = module.params['excluded_paths']
                if excluded:
                    args += ['(']
                    for index, excluded_path in enumerate(excluded):
                        if index:
                            args += ['-o']
                        args += ['-path', excluded_path]
                    args += [')', '-prune', '-o']
                args += ['-' + kind, str(old), '-print0']
                result = subprocess.run(args, capture_output=True, check=False)
                if result.returncode:
                    raise RuntimeError('Ownership scan failed: ' + os.fsdecode(result.stderr))
                for raw in result.stdout.split(b'\0'):
                    if not raw:
                        continue
                    path = os.fsdecode(raw)
                    st = os.lstat(path)
                    if kind == 'uid' and st.st_uid == old:
                        os.lchown(path, new, -1)
                    if kind == 'gid' and st.st_gid == old:
                        os.lchown(path, -1, new)

        ids = [p for p in plan if p['kind'] in ('uid', 'gid')]
        occupied = {u.pw_uid for u in passwd.values()} | {g.gr_gid for g in groupdb.values()} | {p['new'] for p in ids}
        temporary = 60000
        # First release every moving identifier, so cycles and declaration order work.
        for p in ids:
            mutated = True
            while temporary in occupied:
                temporary += 1
            p['temporary'] = temporary
            occupied.add(temporary)
            if p['kind'] == 'uid':
                run(['usermod', '-u', str(temporary), p['name']])
            else:
                run(['groupmod', '-g', str(temporary), p['name']])
                for entry in passwd.values():
                    if entry.pw_gid == p['old']:
                        run(['usermod', '-g', str(temporary), entry.pw_name])
            ownership(p['kind'], p['old'], temporary)
        for p in ids:
            if p['kind'] == 'uid':
                run(['usermod', '-u', str(p['new']), p['name']])
            else:
                run(['groupmod', '-g', str(p['new']), p['name']])
                for entry in pwd.getpwall():
                    if entry.pw_gid == p['temporary']:
                        run(['usermod', '-g', str(p['new']), entry.pw_name])
            ownership(p['kind'], p['temporary'], p['new'])
        for p in plan:
            if p['kind'] == 'home':
                mutated = True
                os.makedirs(os.path.dirname(p['new']), exist_ok=True)
                shutil.move(p['old'], p['new'])
                run(['usermod', '-d', p['new'], p['name']])
        module.exit_json(changed=True, plan=plan)
    except (ValueError, RuntimeError, OSError) as exc:
        module.fail_json(msg=str(exc), plan=plan, changed=mutated)


if __name__ == '__main__':
    main()
