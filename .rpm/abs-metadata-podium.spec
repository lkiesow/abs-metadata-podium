Name:           abs-metadata-podium
Summary:        Audiobookshelf custom metadata provider for Podium Entertainment
Version:        %{appversion}
Release:        1
License:        MIT

BuildArch:      noarch

Source0:        %{name}-%{version}.tar.gz
Source1:        %{name}.service
Source2:        %{name}.conf.example
URL:            https://github.com/lkiesow/%{name}
BuildRoot:      %{_tmppath}/%{name}-root

BuildRequires:     python3-devel
BuildRequires:     pyproject-rpm-macros
BuildRequires:     systemd-rpm-macros
Requires:          python3-flask
Requires:          python3-requests
Requires:          python3-beautifulsoup4
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd


%description
An Audiobookshelf custom metadata provider that searches Podium
Entertainment's website for a title and scrapes metadata and cover art from
the matching book page.


%prep
%autosetup -n %{name}-%{version}


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files abs_metadata_podium

install -p -D -m 0644 \
   %{SOURCE1} \
   %{buildroot}%{_unitdir}/%{name}.service

install -p -D -m 0644 \
   %{SOURCE2} \
   %{buildroot}%{_sysconfdir}/%{name}.conf


%clean
rm -rf %{buildroot}


%pre
# Create user and group if they don't exist
if [ ! $(getent passwd %{name}) ]; then
   useradd --system --user-group --no-create-home --shell /sbin/nologin %{name} > /dev/null 2>&1 || :
fi


%post
%systemd_post %{name}.service


%preun
%systemd_preun %{name}.service


%postun
%systemd_postun_with_restart %{name}.service


%files -f %{pyproject_files}
%{_bindir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}.conf
%{_unitdir}/%{name}.service
%license LICENSE
%doc README.md


%changelog
* Sat Jul 11 2026 Lars Kiesow <lkiesow@uos.de> - 0.1.0-1
- Initial build
