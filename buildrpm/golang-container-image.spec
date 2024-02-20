{{{$version := printf "%s.%s.%s" .major .minor .patch }}}
%global debug_package     %{nil}
%{!?registry: %global registry container-registry.oracle.com/olcne}

%global _name    golang
%global rpm_suffix %{version}-%{release}.%{_build_arch}
%global noarch_suffix %{version}-%{release}.noarch
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
yumdownloader --destdir=${PWD}/rpms \
  golang-%{rpm_suffix} \
  golang-bin-%{rpm_suffix} \
  golang-misc-%{noarch_suffix} \
  golang-docs-%{noarch_suffix} \
  golang-src-%{noarch_suffix} \
  golang-tests-%{noarch_suffix}
%if 0%{?oraclelinux} == 9
%global docker_file ./olm/builds/Dockerfile_ol9
%else
%global docker_file ./olm/builds/Dockerfile
%endif
docker build --network host --pull --build-arg https_proxy=${https_proxy} \
        -t %{docker_tag} -f %{docker_file} .
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
