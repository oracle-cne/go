FROM container-registry.oracle.com/os/oraclelinux:8
COPY rpms /tmp/
RUN dnf install -y gcc &&\
    dnf module disable go-toolset &&\
    dnf config-manager --disable ol8_appstream &&\
    dnf install -y /tmp/*.rpm &&\
    dnf clean all &&\
    rm -rf /var/cache/yum/* /tmp/*.rpm

ENTRYPOINT [ "/usr/bin/bash" ]
