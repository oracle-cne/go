FROM container-registry.oracle.com/os/oraclelinux:8
COPY rpms /tmp/
RUN dnf install -y /tmp/*.rpm &&\
    dnf clean all &&\
    rm -rf /var/cache/yum/* /tmp/*.rpm

FROM container-registry.oracle.com/os/oraclelinux:8-slim
COPY --from=0 /usr/bin/go* /usr/bin/
COPY LICENSE THIRD_PARTY_LICENSES.txt SECURITY.md

ENTRYPOINT [ "/usr/bin/go" ]
