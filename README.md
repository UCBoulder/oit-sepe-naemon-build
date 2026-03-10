RPM Builds for Naemon
=====================

This repo builds all the RPMs needed for our Naemon monitoring cluster.
Spec files are collected here so we can control versions, ensure ABI
compatibility across packages, and deliver updates as a single tested
artifact.

Deployment is handled by
[oit-sepe-naemon-infra](https://github.com/UCBoulder/oit-sepe-naemon-infra).

Packages
--------

| Package            | Upstream                                                        | Description                          |
| :----------------- | :-------------------------------------------------------------- | :----------------------------------- |
| naemon-core        | [naemon/naemon](https://github.com/naemon/naemon)              | Monitoring daemon (Nagios fork)      |
| naemon             | naemon/naemon                                                   | Metapackage                          |
| naemon-livestatus  | naemon/naemon                                                   | Livestatus API for live queries      |
| naemon-vimvault    | naemon/naemon                                                   | Vim syntax for Naemon config         |
| merlin             | [ITRS-Group/monitor-merlin](https://github.com/ITRS-Group/monitor-merlin) | Distributed monitoring (NEB module + daemon) |
| libthruk           | [sni/Thruk](https://github.com/sni/Thruk)                      | Perl library for Thruk               |
| thruk              | sni/Thruk                                                       | Monitoring web UI                    |

Build Pipeline
--------------

The CI pipeline (`build.yml`) runs on every push. Jobs have
dependencies because some packages must be compiled against headers
from others:

```
naemon-core ──┬── naemon-livestatus
              ├── naemon-vimvault
              ├── merlin              (links against naemon event broker API)
              └── naemon

libthruk ──────── thruk               (thruk BuildRequires libthruk)
```

The `publish-rpms` job runs only on tag pushes and creates a GitHub
Release with all RPM artifacts attached.

How to Release
--------------

1. Create a branch and update spec files as needed. Push and iterate
   until CI is green.
2. Merge your PR into main.
3. Tag and push from main:

```
git checkout main
git pull
git tag cub-X.Y.Z
git push origin cub-X.Y.Z
```

4. Watch [Actions](https://github.com/UCBoulder/oit-sepe-naemon-build/actions)
   to confirm the build and publish succeed.
5. Verify the release appears under
   [Releases](https://github.com/UCBoulder/oit-sepe-naemon-build/releases)
   with all expected RPMs attached.

Tags use the `cub-X.Y.Z` convention (CU Boulder). Use your judgment on
versioning — bump the minor for package version upgrades, patch for
rebuild-only changes (like a merlin release bump).

If you need to redo a tag:

```
git tag -d cub-X.Y.Z
git push origin :refs/tags/cub-X.Y.Z
```

Then delete the corresponding release from the GitHub UI.

Merlin ABI Compatibility
------------------------

**This is the most important thing to know about this repo.**

Merlin's NEB module (`merlin.so`) is compiled against naemon-core's
event broker API headers. When naemon-core has a major version bump
(e.g., 1.4.x to 1.5.x), the event broker API version changes. If
merlin is not rebuilt against the new headers, naemon will refuse to
load it:

```
Module '/usr/lib64/merlin/merlin.so' is using an incompatible version (v6)
of the event broker API (current version: v8). Module will be unloaded.
```

The CI pipeline always builds merlin against the naemon-core from the
same run, so the binary is correct. But there is a downstream
deployment gotcha: if merlin's RPM version string doesn't change (same
`Version` and `Release`), `dnf` will see it as already installed and
skip the upgrade — leaving the old incompatible binary in place.

**Fix:** When bumping naemon-core to a new version, also bump the
`Release:` field in `merlin.spec` (e.g., `0` to `1`). This gives the
RPM a new version string so `dnf` will upgrade it.

libthruk v3.26+ Notes
---------------------

Starting with v3.26, libthruk migrated from bundling ~80 Perl modules
to using system packages from EPEL. The `libthruk.spec` lists ~37
`Requires:` for system Perl modules. If upgrading libthruk to a new
major version, compare the upstream spec's dependency list against ours
to catch any additions or removals.
