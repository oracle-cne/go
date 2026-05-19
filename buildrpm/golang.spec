{{{$version := printf "%s.%s.%s" .major .minor .patch }}}
%undefine _missing_build_ids_terminate_build

%global bcond_with strict_fips

# build ids are not currently generated:
# https://code.google.com/p/go/issues/detail?id=5238
#
# also, debuginfo extraction currently fails with
# "Failed to write file: invalid section alignment"
%global debug_package %{nil}

# we are shipping the full contents of src in the data subpackage, which
# contains binary-like things (ELF data for tests, etc)
%global _binaries_in_noarch_packages_terminate_build 0

# Do not check any files in doc or src for requires
%global __requires_exclude_from ^(%{_datadir}|/usr/lib)/%{name}/(doc|src)/.*$

# Don't alter timestamps of especially the .a files (or else go will rebuild later)
# Actually, don't strip at all since we are not even building debug packages and this corrupts the dwarf testdata
%global __strip /bin/true

# rpmbuild magic to keep from having meta dependency on libc.so.6
%define _use_internal_dependency_generator 0
%define __find_requires %{nil}
%global __spec_install_post /usr/lib/rpm/check-rpaths   /usr/lib/rpm/check-buildroot  \
  /usr/lib/rpm/brp-compress

# Define GOROOT macros
%global goroot          %{_prefix}/lib/%{name}
%global gopath          %{_datadir}/gocode
%global golang_arches   x86_64 aarch64 ppc64le s390x
%global golibdir        %{_libdir}/%{name}

# Golang build options.

# Build golang using external/internal(close to cgo disabled) linking.
%ifarch x86_64 ppc64le %{arm} aarch64 s390x
%global external_linker 1
%else
%global external_linker 0
%endif

# Build golang with cgo enabled/disabled(later equals more or less to internal linking).
%ifarch x86_64 ppc64le %{arm} aarch64 s390x
%global cgo_enabled 1
%else
%global cgo_enabled 0
%endif

# Use golang/gcc-go as bootstrap compiler
%ifarch %{golang_arches}
%global golang_bootstrap 1
%else
%global golang_bootstrap 0
%endif

# Controls what ever we fail on failed tests
%ifarch x86_64 %{arm} aarch64 ppc64le s390x
%global fail_on_tests 1
%else
%global fail_on_tests 0
%endif

# Build golang shared objects for stdlib
%ifarch 0
%global shared 1
%else
%global shared 0
%endif

%ifarch x86_64
%global gohostarch  amd64
%endif
%ifarch %{arm}
%global gohostarch  arm
%endif
%ifarch aarch64
%global gohostarch  arm64
%endif
%ifarch ppc64
%global gohostarch  ppc64
%endif
%ifarch ppc64le
%global gohostarch  ppc64le
%endif
%ifarch s390x
%global gohostarch  s390x
%endif

# golang release version
%global version {{{$version}}}

Name:           golang
Version:        %{version}
Release:        1%{?dist}

Summary:        The Go Programming Language
# source tree includes several copies of Mark.Twain-Tom.Sawyer.txt under Public Domain
License:        BSD and Public Domain
URL:            http://golang.org/
Source0:        %{name}-%{version}.tar.bz2

# The compiler is written in Go. Needs go(1.4+) compiler for build.
# Actual Go based bootstrap compiler provided by above source.
# For OpenSSL FIPS
BuildRequires:  openssl-devel
# for tests
BuildRequires:  pcre-devel, glibc-static, perl

BuildRequires:  golang >= 1.19.0
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  clang
BuildRequires:  rpm
BuildRequires:  cpio

%if 0%{?oraclelinux} == 7
BuildRequires: libstdc++
BuildRequires: libstdc++-static
%endif

Provides:       go = %{version}-%{release}
Requires:       %{name}-bin = %{version}-%{release}
Requires:       %{name}-src = %{version}-%{release}
Requires:       openssl-devel
Requires:       diffutils

# Having documentation separate was broken
Obsoletes:      %{name}-docs < 1.1-4

# RPM can't handle symlink -> dir with subpackages, so merge back
Obsoletes:      %{name}-data < 1.1.1-4

# These are the only RHEL/Fedora architectures that we compile this package for
ExclusiveArch:  %{golang_arches}

Source100:      golang-gdbinit
Source101:      golang-prelink.conf
Patch0:         build-goboring.sh.patch

%description
%{summary}.

%package       docs
Summary:       Golang compiler docs
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch
Obsoletes:     %{name}-docs < 1.1-4

%description   docs
%{summary}.

%package       misc
Summary:       Golang compiler miscellaneous sources
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch

%description   misc
%{summary}.

%package       tests
Summary:       Golang compiler tests for stdlib
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch

%description   tests
%{summary}.

%package        src
Summary:        Golang compiler source tree
BuildArch:      noarch

%description    src
%{summary}

%package        bin
Summary:        Golang core compiler tools
Requires:       %{name} = %{version}-%{release}

# We strip the meta dependency, but go does require glibc.
# This is an odd issue, still looking for a better fix.
Requires:       glibc
Requires:       /usr/bin/gcc
%description    bin
%{summary}

# Workaround old RPM bug of symlink-replaced-with-dir failure
%pretrans -p <lua>
for _,d in pairs({"api", "doc", "include", "lib", "src"}) do
  path = "%{goroot}/" .. d
  if posix.stat(path, "type") == "link" then
    os.remove(path)
    posix.mkdir(path)
  end
end

%if %{shared}
%package        shared
Summary:        Golang shared object libraries

%description    shared
%{summary}.
%endif

%prep
%setup -q -n %{name}-%{version}
%patch0

# OL8 uses a very old glibc that does not support the atomics
# used in src/runtime/race/race_linux_arm64.syso.  Copy an
# older version that does not use those symbols over top so
# that it is compatible.
%ifarch aarch64
%if 0%{?oraclelinux} == 8
cp %{buildroot}/olm/builds/race_linux_arm64.syso %{buildroot}/src/runtime/race/race_linux_arm64.syso
%endif
%endif

%build
set -xe
# print out system information
uname -a
cat /proc/cpuinfo
cat /proc/meminfo

# bootstrap compiler GOROOT
%if !%{golang_bootstrap}
export GOROOT_BOOTSTRAP=/
%else
export GOROOT_BOOTSTRAP=/opt/rh/go-toolset-1.10/root/usr/lib/go-toolset-1.10-golang
%endif

# set up final install location
export GOROOT_FINAL=%{goroot}

export GOHOSTOS=linux
export GOHOSTARCH=%{gohostarch}

# Install the boringssl source rpm locally
# This is done to override the in-repo builds
# of boringssl
mkdir boringssl-rpm
pushd boringssl-rpm
%if 0%{?oraclelinux} > 7
dnf download boringssl-fips.20210429
%else
yumdownloader boringssl-fips.20210429
%endif
rpm2cpio boringssl*.rpm | cpio -idv
popd

mkdir -p boringssl/include/openssl
mkdir -p boringssl/build/crypto/
mkdir -p boringssl/build/ssl
mkdir -p boringssl/build/decrepit

cp -r boringssl-rpm/usr/include/boringssl/* boringssl/include/openssl
cp boringssl-rpm/usr/lib64/boringssl/libcrypto.a boringssl/build/crypto/libcrypto.a
cp boringssl-rpm/usr/lib64/boringssl/libssl.a boringssl/build/ssl/libssl.a
cp boringssl-rpm/usr/lib64/boringssl/libdecrepit.a boringssl/build/decrepit/libdecrepit.a

mkdir -p boring/godriver

ln -s `pwd`/boringssl boring/boringssl
cp ./src/crypto/internal/boring/goboringcrypto.h ./boring/godriver/
sh ./src/crypto/internal/boring/build-goboring.sh

# Copy the newly built boringssl archive over
# the existing one
cp boring/godriver/goboringcrypto_linux_*.syso ./src/crypto/internal/boring/syso

pushd src
# use our gcc options for this build, but store gcc as default for compiler
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
export CC="gcc"
export CC_FOR_TARGET="gcc"
export GOOS=linux
export GOARCH=%{gohostarch}

DEFAULT_GO_LD_FLAGS=""
%if !%{external_linker}
export GO_LDFLAGS="-linkmode internal $DEFAULT_GO_LD_FLAGS"
%else
# Only pass a select subset of the external hardening flags. We do not pass along
# the default $RPM_LD_FLAGS as on certain arches Go does not fully, correctly support
# building in PIE mode.
export GO_LDFLAGS="\"-extldflags=-Wl,-z,now,-z,relro\" $DEFAULT_GO_LD_FLAGS"
%endif
%if !%{cgo_enabled}
export CGO_ENABLED=0
%endif
./make.bash --no-clean
popd

# build shared std lib
%if %{shared}
GOROOT=$(pwd) PATH=$(pwd)/bin:$PATH go install -buildmode=shared std
%endif


%install

rm -rf $RPM_BUILD_ROOT

# create the top level directories
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{goroot}

# remove bootstrap binaries
rm -rf pkg/bootstrap/bin

install -d -p -m 0755 %{buildroot}/usr/include/boringssl
install -d -p -m 0755 %{buildroot}/usr/lib64/boringssl
install -d -p -m 0755 %{buildroot}/usr/lib/golang/src/boringssl
install -D -p -m 0644 boringssl/include/openssl/* %{buildroot}/usr/include/boringssl
install -D -p -m 0644 boringssl/build/crypto/libcrypto.a %{buildroot}/usr/lib64/boringssl/libcrypto.a
install -D -p -m 0644 boringssl/build/ssl/libssl.a %{buildroot}/usr/lib64/boringssl/libssl.a
install -D -p -m 0644 boringssl/build/decrepit/libdecrepit.a %{buildroot}/usr/lib64/boringssl/libdecrepit.a
cp -r boringssl-rpm/usr %{buildroot}/usr/lib/golang/src/boringssl

# install everything into libdir (until symlink problems are fixed)
# https://code.google.com/p/go/issues/detail?id=5830
cp -apv api bin doc lib pkg src misc test VERSION \
   $RPM_BUILD_ROOT%{goroot}

# Add go.env
install -D -p -m 444 go.env $RPM_BUILD_ROOT%{goroot}

# bz1099206
find $RPM_BUILD_ROOT%{goroot}/src -exec touch -r $RPM_BUILD_ROOT%{goroot}/VERSION "{}" \;
# and level out all the built archives
touch $RPM_BUILD_ROOT%{goroot}/pkg
find $RPM_BUILD_ROOT%{goroot}/pkg -exec touch -r $RPM_BUILD_ROOT%{goroot}/pkg "{}" \;
# generate the spec file ownership of this source tree and packages
cwd=$(pwd)
src_list=$cwd/go-src.list
pkg_list=$cwd/go-pkg.list
shared_list=$cwd/go-shared.list
misc_list=$cwd/go-misc.list
docs_list=$cwd/go-docs.list
tests_list=$cwd/go-tests.list
rm -f $src_list $pkg_list $docs_list $misc_list $tests_list $shared_list
touch $src_list $pkg_list $docs_list $misc_list $tests_list $shared_list
pushd $RPM_BUILD_ROOT%{goroot}
    find src/ -type d -a \( ! -name testdata -a ! -ipath '*/testdata/*' \) -printf '%%%dir %{goroot}/%p\n' >> $src_list
    find src/ ! -type d -a \( ! -ipath '*/testdata/*' -a ! -name '*_test*.go' \) -printf '%{goroot}/%p\n' >> $src_list

    find bin/ pkg/ -type d -a ! -path '*_dynlink/*' -printf '%%%dir %{goroot}/%p\n' >> $pkg_list
    find bin/ pkg/ ! -type d -a ! -path '*_dynlink/*' -printf '%{goroot}/%p\n' >> $pkg_list

    find doc/ -type d -printf '%%%dir %{goroot}/%p\n' >> $docs_list
    find doc/ ! -type d -printf '%{goroot}/%p\n' >> $docs_list

    find misc/ -type d -printf '%%%dir %{goroot}/%p\n' >> $misc_list
    find misc/ ! -type d -printf '%{goroot}/%p\n' >> $misc_list

%if %{shared}
    mkdir -p %{buildroot}/%{_libdir}/
    mkdir -p %{buildroot}/%{golibdir}/
    for file in $(find .  -iname "*.so" ); do
        chmod 755 $file
        mv  $file %{buildroot}/%{golibdir}
        pushd $(dirname $file)
        ln -fs %{golibdir}/$(basename $file) $(basename $file)
        popd
        echo "%%{goroot}/$file" >> $shared_list
        echo "%%{golibdir}/$(basename $file)" >> $shared_list
    done

    find pkg/*_dynlink/ -type d -printf '%%%dir %{goroot}/%p\n' >> $shared_list
    find pkg/*_dynlink/ ! -type d -printf '%{goroot}/%p\n' >> $shared_list
%endif


    find test/ -type d -printf '%%%dir %{goroot}/%p\n' >> $tests_list
    find test/ ! -type d -printf '%{goroot}/%p\n' >> $tests_list
    find src/ -type d -a \( -name testdata -o -ipath '*/testdata/*' \) -printf '%%%dir %{goroot}/%p\n' >> $tests_list
    find src/ ! -type d -a \( -ipath '*/testdata/*' -o -name '*_test*.go' \) -printf '%{goroot}/%p\n' >> $tests_list
    # this is only the zoneinfo.zip
    find lib/ -type d -printf '%%%dir %{goroot}/%p\n' >> $tests_list
    find lib/ ! -type d -printf '%{goroot}/%p\n' >> $tests_list
popd

# remove the doc Makefile
rm -rfv $RPM_BUILD_ROOT%{goroot}/doc/Makefile

# put binaries to bindir, linked to the arch we're building,
# leave the arch independent pieces in {goroot}
mkdir -p $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}
ln -sf %{goroot}/bin/go $RPM_BUILD_ROOT%{_bindir}/go
ln -sf %{goroot}/bin/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt

# ensure these exist and are owned
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/github.com
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/bitbucket.org
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/code.google.com/p
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/golang.org/x

# gdbinit
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d
cp -av %{SOURCE100} $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d/golang.gdb

# prelink blacklist
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d
cp -av %{SOURCE101} $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d/golang.conf

# Quick fix for the rhbz#2014704
sed -i 's/const defaultGO_LDSO = `.*`/const defaultGO_LDSO = ``/' $RPM_BUILD_ROOT%{goroot}/src/internal/buildcfg/zbootstrap.go

%check
export GOROOT=$(pwd -P)
export PATH="$GOROOT"/bin:"$PATH"
cd src

# Add some sanity checks.
echo "GO VERSION:"
go version

echo "GO ENVIRONMENT:"
go env

export CC="gcc"
export CFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"
%if !%{external_linker}
export GO_LDFLAGS="-linkmode internal"
%else
export GO_LDFLAGS="-extldflags '$RPM_LD_FLAGS'"
%endif
%if !%{cgo_enabled} || !%{external_linker}
export CGO_ENABLED=0
%endif

# make sure to not timeout
export GO_TEST_TIMEOUT_SCALE=2

export GO_TEST_RUN=""
%ifarch aarch64
  export GO_TEST_RUN="-run=!testshared"
%endif

%if %{fail_on_tests}

# TestEd25519Vectors needs network connectivity but it should be cover by
# this test https://pkgs.devel.redhat.com/cgit/tests/golang/tree/Regression/internal-testsuite/runtest.sh#n127

./run.bash --no-rebuild -v -v -v -k $GO_TEST_RUN

# Run tests with FIPS enabled.
export GOLANG_FIPS=1
pushd crypto
  # Run all crypto tests but skip TLS, we will run FIPS specific TLS tests later
  go test $(go list ./... | grep -v tls) -v
  # Check that signature functions have parity between boring and notboring
  CGO_ENABLED=0 go test $(go list ./... | grep -v tls) -v
popd
# Run all FIPS specific TLS tests
pushd crypto/tls
  go test -v -run "Boring"
popd
%else
./run.bash --no-rebuild -v -v -v -k || :
%endif
cd ..

%files

%doc LICENSE PATENTS
# VERSION has to be present in the GOROOT, for `go install std` to work
%doc %{goroot}/VERSION
%dir %{goroot}/doc
%doc %{goroot}/doc/*

# go files
%dir %{goroot}
%exclude %{goroot}/bin/
%exclude %{goroot}/pkg/
%exclude %{goroot}/src/
%exclude %{goroot}/doc/
%exclude %{goroot}/misc/
%exclude %{goroot}/test/

%{goroot}/*

# ensure directory ownership, so they are cleaned up if empty
%dir %{gopath}
%dir %{gopath}/src
%dir %{gopath}/src/github.com/
%dir %{gopath}/src/bitbucket.org/
%dir %{gopath}/src/code.google.com/
%dir %{gopath}/src/code.google.com/p/
%dir %{gopath}/src/golang.org
%dir %{gopath}/src/golang.org/x

# gdbinit (for gdb debugging)
%{_sysconfdir}/gdbinit.d

# prelink blacklist
%{_sysconfdir}/prelink.conf.d

%files -f go-src.list src

%files -f go-docs.list docs

%files -f go-misc.list misc

%files -f go-tests.list tests

%files -f go-pkg.list bin
%{_bindir}/go
%{_bindir}/gofmt

%if %{shared}
%files -f go-shared.list shared
%endif

%license LICENSE
/usr/lib64/boringssl/*
/usr/include/boringssl/*

%changelog
* {{{.changelog_timestamp}}} - {{{$version}}}-1
- Adopt go {{{$version}}}
