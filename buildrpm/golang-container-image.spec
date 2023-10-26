{{{$version := printf "%s.%s.%s" .major .minor .patch }}}
%global debug_package     %{nil}
%{!?registry: %global registry container-registry.oracle.com/olcne}

%global _name    golang
%global rpm_name %{_name}-%{version}-%{release}.%{_build_arch}
%global docker_tag %{registry}/%{_name}:v%{version}

# golang release version
%global version {{{$version}}}

%global _buildhost build-ol%{?oraclelinux}-%{?_arch}.oracle.com

Name:           golang-container-image
Version:        %{version}
Release:        1%{?dist}
Summary:        The Go Programming Language
License:        ASL 2.0
Group:          System/Management
URL:            https://github.com/golang/go
Vendor:         Oracle America
Source0:        %{name}-%{version}.tar.bz2

%description
The Go Programming Language

%prep
%setup -q -n %{name}-%{version}

%build
yum clean all
yumdownloader --destdir=${PWD}/rpms %{rpm_name}

docker build --pull --build-arg https_proxy=${https_proxy} \
        -t %{docker_tag} -f ./olm/builds/Dockerfile .
docker save -o %{_name}.tar %{docker_tag}

%install
%__install -D -m 644 %{_name}.tar %{buildroot}/usr/local/share/olcne/%{_name}.tar

%files
# TODO: Add TPL
%license LICENSE
/usr/local/share/olcne/%{_name}.tar

%changelog
* {{{.changelog_timestamp}}} - {{{$version}}}-1
- Initial files for golang
