# -*- coding: utf-8; mode: dockerfile; -*-
FROM registry.fedoraproject.org/fedora:42
LABEL maintainer="Tom Vaughan <tvaughan@tocino.cl>"

LABEL traefik.enable="true"
LABEL traefik.http.routers.sumario-backend.entrypoints="sumario"
LABEL traefik.http.routers.sumario-backend.rule="PathPrefix(`/`)"
LABEL traefik.http.routers.sumario-backend.service="sumario-backend@docker"
LABEL traefik.http.routers.sumario-backend.tls="true"
LABEL traefik.http.services.sumario-backend.loadbalancer.server.port="3000"

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC

RUN sudo dnf config-manager setopt install_weak_deps=0                          \
    && rm -f /etc/yum.repos.d/fedora-cisco-openh264.repo

RUN rm -rf /var/cache/{dnf,yum}/*                                               \
    && dnf install -y                                                           \
        automake                                                                \
        dumb-init                                                               \
        gcc                                                                     \
        git                                                                     \
        libpq-devel                                                             \
        make                                                                    \
        nodejs-npm                                                              \
        postgresql                                                              \
        python3-devel                                                           \
        python3-pip                                                             \
    && rm -rf /var/cache/{dnf,yum}/*                                            \
    && dnf clean all

RUN python3 -m pip install uv==0.7.2

RUN npm install -g uglify-js uglifycss

WORKDIR /mnt/workdir

ENTRYPOINT ["dumb-init", "--"]

CMD ["bash"]
