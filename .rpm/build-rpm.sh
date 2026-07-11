#!/bin/bash

set -eux

dnf install -y epel-release
/usr/bin/crb enable
dnf install -y rpmdevtools python3-devel pyproject-rpm-macros systemd-rpm-macros
rpmdev-setuptree

echo "%appversion ${2}" >>~/.rpmmacros
cp "/rpmbuild/${1}" ~/rpmbuild/SOURCES/
cp /rpmbuild/.rpm/abs-metadata-podium.service ~/rpmbuild/SOURCES/
cp /rpmbuild/.rpm/abs-metadata-podium.conf.example ~/rpmbuild/SOURCES/
cp /rpmbuild/.rpm/abs-metadata-podium.spec ~/rpmbuild/SPECS/

# Dynamic BuildRequires (from %generate_buildrequires) aren't known until the
# package's own build system is consulted, and each pass only discovers the
# next missing requirement, so loop discover+install until it's satisfied.
for _ in 1 2 3 4 5; do
   rm -f ~/rpmbuild/SRPMS/abs-metadata-podium-*.buildreqs.nosrc.rpm
   rpmbuild -br ~/rpmbuild/SPECS/abs-metadata-podium.spec && break
   dnf builddep -y ~/rpmbuild/SRPMS/abs-metadata-podium-*.buildreqs.nosrc.rpm
done

rpmbuild -ba ~/rpmbuild/SPECS/abs-metadata-podium.spec

# Fail the build here (not just later, on a target machine) if the package
# can't actually be installed with its declared Requires.
dnf install -y ~/rpmbuild/RPMS/noarch/abs-metadata-podium*.rpm

cp ~/rpmbuild/RPMS/noarch/abs-metadata-podium*.rpm /rpmbuild/
