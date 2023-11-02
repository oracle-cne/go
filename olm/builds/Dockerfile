FROM container-registry.oracle.com/os/oraclelinux:9
COPY rpms /tmp/
RUN dnf install -y /tmp/*.rpm &&\
    dnf clean all &&\
    rm -rf /var/cache/yum/* /tmp/*.rpm

ENTRYPOINT [ "/usr/bin/bash" ]
