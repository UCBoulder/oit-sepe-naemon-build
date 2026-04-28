%define mod_path /etc/merlin

%define init_scripts --with-initdirectory=%_sysconfdir/init.d --with-initscripts=data/merlind
%if 0%{?suse_version}
%define mysqld mariadb
%define daemon_user naemon
%define daemon_group naemon
%endif
%if 0%{?rhel} >= 7
%define mysqld mariadb
%define daemon_user naemon
%define daemon_group naemon
%define init_scripts %{nil}
%endif
%define operator_group mon_operators
%define naemon_confdir %_sysconfdir/naemon/

%undefine _disable_source_fetch

Summary: The merlin daemon is a multiplexing event-transport program
Name: merlin
Version: 2024.10.14
Release: 5
License: GPLv2
URL: https://github.com/ITRS-Group/monitor-merlin/
Source0: https://github.com/ITRS-Group/monitor-merlin/archive/refs/tags/v%{version}.tar.gz

# TEMPORARY: Patch for naemon 1.5.1 check_timeout API change.
# Remove this Patch0 declaration and the %patch0 invocation below when
# merlin releases a version that includes the fix. Also bump Version/
# Release and update the merlin dependency filenames in build.yml at
# that time.
# Upstream PR: https://github.com/ITRS-Group/monitor-merlin/pull/174
Patch0: merlin-0001-check_timeout-naemon-1.5.1.patch

BuildRoot: %{_tmppath}/monitor-%{name}-%{version}
Requires: libaio
Requires: merlin-apps = %{version}-%{release}
Requires: monitor-merlin
Requires: naemon-core
Requires: glib2
Requires: libsodium
Requires: systemd
BuildRequires: libsodium-devel
BuildRequires: mariadb-devel
BuildRequires: naemon-devel
BuildRequires: python39
BuildRequires: gperf
BuildRequires: check-devel
BuildRequires: autoconf, automake, libtool
BuildRequires: glib2-devel
BuildRequires: libdbi-devel
BuildRequires: pkgconfig
BuildRequires: pkgconfig(gio-unix-2.0)

%description
The merlin daemon is a multiplexing event-transport program designed to
link multiple Nagios instances together. It can also inject status
data into a variety of databases, using libdbi.

%package slim
Summary: Slim version of the merlin daemon
Requires: libaio
Requires: merlin-apps-slim = %{version}-%{release}
Requires: glib2
BuildRequires: naemon-devel
BuildRequires: python39
BuildRequires: gperf
BuildRequires: check-devel
BuildRequires: autoconf, automake, libtool
BuildRequires: glib2-devel
BuildRequires: libdbi-devel
BuildRequires: pkgconfig
BuildRequires: pkgconfig(gio-unix-2.0)

%description slim
The merlin daemon is a multiplexing event-transport program designed to
link multiple Nagios instances together. It can also inject status
data into a variety of databases, using libdbi. This version of the package is
slim version that installs fewer dependencies.

%package -n monitor-merlin
Summary: A Nagios module designed to communicate with the Merlin daemon
Requires: naemon-core, merlin = %version-%release
Requires: systemd

%description -n monitor-merlin
monitor-merlin is an event broker module running inside Nagios. Its
only purpose in life is to send events from the Nagios core to the
merlin daemon, which then takes appropriate action.

%package -n monitor-merlin-slim
Summary: A Nagios module designed to communicate with the Merlin daemon
Requires: naemon-core, merlin-slim = %version-%release

%description -n monitor-merlin-slim
monitor-merlin is an event broker module running inside Nagios. Its
only purpose in life is to send events from the Nagios core to the
merlin daemon, which then takes appropriate action.

%package apps
Summary: Applications used to set up and aid a merlin/ninja installation
Requires: rsync
Requires: systemd
Requires: sudo
Requires: openssh-server
Requires: naemon-livestatus
# php-cli for mon node tree
Requires: php-cli
Requires: procps-ng

%description apps
This package contains standalone applications required by Ninja and
Merlin in order to make them both fully support everything that a
fully fledged op5 Monitor install is supposed to handle.
'mon' works as a single entry point wrapper and general purpose helper
tool for those applications and a wide variety of other different
tasks, such as showing monitor's configuration files, calculating
sha1 checksums and the latest changed such file, as well as
preparing object configuration for pollers, helping with ssh key
management and allround tasks regarding administering a distributed
network monitoring setup.


%package apps-slim
Summary: Applications used to set up and aid a merlin/ninja installation
Requires: rsync
Requires: openssh
Requires: openssh-clients
# php-cli for mon node tree
Requires: php-cli
Requires: procps-ng
%if 0%{?rhel} >= 8
Requires: python3-docopt
Requires: python3-cryptography
Requires: python3-paramiko
%else
Requires: python36-docopt
Requires: python36-cryptography
Requires: python36-paramiko
%endif # 0%{?rhel} >= 8

%description apps-slim
This package contains standalone applications required by Ninja and
Merlin in order to make them both fully support everything that a
fully fledged op5 Monitor install is supposed to handle.
'mon' works as a single entry point wrapper and general purpose helper
tool for those applications and a wide variety of other different
tasks, such as showing monitor's configuration files, calculating
sha1 checksums and the latest changed such file, as well as
preparing object configuration for pollers, helping with ssh key
management and allround tasks regarding administering a distributed
network monitoring setup.

%prep
%setup -q -n monitor-%{name}-%{version}
%patch0 -p1

%build
echo %{version} > .version_number
autoreconf -i -s
%configure --disable-auto-postinstall --with-pkgconfdir=%mod_path --with-naemon-config-dir=%naemon_confdir/module-conf.d --with-naemon-user=%daemon_user --with-naemon-group=%daemon_user --with-logdir=%{_localstatedir}/log/merlin --datarootdir=%_datadir %init_scripts

%__make V=1
%__make V=1 check || true

%install
%make_install naemon_user=$(id -un) naemon_group=$(id -gn)

ln -s ../../../../usr/bin/merlind %buildroot/%mod_path/merlind
ln -s ../../../../%_libdir/merlin/import %buildroot/%mod_path/import
ln -s ../../../../%_libdir/merlin/rename %buildroot/%mod_path/rename
ln -s ../../../../%_libdir/merlin/showlog %buildroot/%mod_path/showlog
ln -s ../../../../%_libdir/merlin/merlin.so %buildroot/%mod_path/merlin.so
ln -s op5 %buildroot/%_bindir/mon

cp cukemerlin %buildroot/%_bindir/cukemerlin
cp -r apps/tests %buildroot/usr/share/merlin/app-tests


# nrpe-merlin.cfg intentionally NOT installed. The commands it defines
# reference /opt/plugins/ paths from the upstream op5 Monitor distribution
# that don't exist in our environment. Our naemon/merlin NRPE checks are
# deployed via Ansible in check_naemon.cfg instead.

%{__install} -D -m 644 merlind.service %{buildroot}%{_unitdir}/merlind.service
# Ensure oconf dir exists
%{__install} -d %{buildroot}%{naemon_confdir}/oconf

%check
python3 tests/pyunit/test_log.py --verbose
python3 tests/pyunit/test_oconf.py --verbose

mkdir -p %buildroot%_localstatedir/merlin

%post
systemctl daemon-reload || :
systemctl enable merlind.service || :

# chown old cached nodesplit data, so it can be deleted
chown -R %daemon_user:%daemon_group %_localstatedir/cache/merlin

# Create operator group for use in sudoers
getent group %operator_group > /dev/null || groupadd %operator_group

# In managed (Ansible) deployments, the playbook handles the merlind
# restart sequence to avoid ABI mismatch. For standalone RPM upgrades,
# only restart merlind when it is already running.
if command -v systemctl >/dev/null 2>&1 && systemctl -q is-active merlind.service; then
    systemctl try-restart merlind.service || :
fi

%preun -n monitor-merlin
if [ $1 -eq 0 ]; then
    systemctl stop merlind || :
fi

%postun -n monitor-merlin
# Intentionally empty — the nrpe restart that was here was removed
# because nrpe picks up config changes on reload and the merlin
# package uninstall doesn't require an nrpe bounce.
:

%post -n monitor-merlin
# In managed (Ansible) deployments, the playbook handles the naemon
# restart sequence to avoid ABI mismatch. For standalone RPM upgrades,
# only restart naemon when it is already running so updated merlin.so
# is picked up without starting a stopped service.
if command -v systemctl >/dev/null 2>&1 && systemctl -q is-active naemon.service; then
    systemctl try-restart naemon.service || :
fi

%files
%defattr(-,root,root)
%dir %attr(750, %daemon_user, %daemon_group) %mod_path
%attr(660, %daemon_user, %daemon_group) %config(noreplace) %mod_path/merlin.conf
%_datadir/merlin/sql
%mod_path/merlind
%_bindir/merlind
%_libdir/merlin/install-merlin.sh
%config(noreplace) %_sysconfdir/logrotate.d/merlin
%{_unitdir}/merlind.service
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/lib/merlin
%attr(775, %daemon_user, %daemon_group) %dir %_localstatedir/lib/merlin/binlogs
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/run/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/cache/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/cache/merlin/config
%exclude %_libdir/merlin/mon/test.py*
%exclude %_bindir/cukemerlin
%exclude /usr/share/merlin/app-tests/
%doc %{_docdir}/merlin/README.md
%doc %{_docdir}/merlin/CHANGELOG.md

%files -n monitor-merlin
%defattr(-,root,root)
%_libdir/merlin/merlin.*
%mod_path/merlin.so
%attr(-, %daemon_user, %daemon_group) %naemon_confdir/module-conf.d/merlin.cfg
%attr(-, %daemon_user, %daemon_group) %dir %naemon_confdir/oconf
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/lib/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/log/merlin
%attr(0440, root, root) %{_sysconfdir}/sudoers.d/merlin

%files apps
%defattr(-,root,root)
%_libdir/merlin/import
%_libdir/merlin/showlog
%_libdir/merlin/rename
%_libdir/merlin/oconf
%_libdir/merlin/keygen
%mod_path/import
%mod_path/showlog
%mod_path/rename
%_libdir/merlin/mon
%_bindir/mon
%_bindir/op5
%exclude %_libdir/merlin/mon/check.py
%exclude %_libdir/merlin/mon/containerhealth.py

%attr(600, root, root) %_libdir/merlin/mon/syscheck/db_mysql_check.sh
%attr(600, root, root) %_libdir/merlin/mon/syscheck/fs_ext_state.sh

%exclude %_libdir/merlin/mon/test.py*
%exclude %_libdir/merlin/merlin.*

%files slim
%defattr(-,root,root)
%attr(660, %daemon_user, %daemon_group) %config(noreplace) %mod_path/merlin.conf
%mod_path/merlind
%_bindir/merlind
%_libdir/merlin/install-merlin.sh
%config(noreplace) %_sysconfdir/logrotate.d/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/lib/merlin
%attr(775, %daemon_user, %daemon_group) %dir %_localstatedir/lib/merlin/binlogs
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/log/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/run/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/cache/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/cache/merlin/config
%doc %{_docdir}/merlin/README.md
%doc %{_docdir}/merlin/CHANGELOG.md

%files -n monitor-merlin-slim
%defattr(-,root,root)
%_libdir/merlin/merlin.*
%mod_path/merlin.so
%attr(-, %daemon_user, %daemon_group) %naemon_confdir/module-conf.d/merlin.cfg
%attr(-, %daemon_user, %daemon_group) %dir %naemon_confdir/oconf
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/lib/merlin
%attr(-, %daemon_user, %daemon_group) %dir %_localstatedir/log/merlin
%attr(0440, root, root) %{_sysconfdir}/sudoers.d/merlin

%files apps-slim
%defattr(-,root,root)
%_libdir/merlin/oconf
%_libdir/merlin/mon
%_libdir/merlin/keygen
%_bindir/mon
%_bindir/op5
%_bindir/merlin_cluster_tools
%exclude %_libdir/merlin/mon/check.py

%attr(600, root, root) %_libdir/merlin/mon/syscheck/db_mysql_check.sh
%attr(600, root, root) %_libdir/merlin/mon/syscheck/fs_ext_state.sh

%exclude %_libdir/merlin/mon/test.py*
%exclude %_libdir/merlin/merlin.*

%clean
rm -rf %buildroot

%changelog
* Mon Apr 28 2026 Eric Schoeller <eric.schoeller@colorado.edu>
- SEPE-1064: Mark logrotate config as %config(noreplace)
- Remove unnecessary Requires: mariadb-server, nrpe, libdbi, libdbi-dbd-mysql, python2-PyMySQL
- Remove unconditional naemon restart from %post -n monitor-merlin
- Bump Release to 5
* Thu Apr 09 2026 Eric Schoeller <eric.schoeller@colorado.edu>
- SEPE-1064: Remove dead code from %post (DB, log import, sed, nrpe restart)
- Stop installing nrpe-merlin.cfg (references non-existent /opt/plugins/ paths)
- Bump Release to 4
* Thu Feb 08 2024 Will Haines <william.haines@colorado.edu>
- Fork for CU Boulder
* Thu Feb 11 2021 Aksel Sjögren <asjogren@itrsgroup.com>
- Adapt for building on el8.
* Tue Mar 17 2009 Andreas Ericsson <ae@op5.se>
- Initial specfile creation.
