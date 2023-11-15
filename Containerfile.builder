# -*- coding: utf-8; mode: dockerfile; -*-
FROM registry.fedoraproject.org/fedora:39
LABEL maintainer="Tom Vaughan <tvaughan@tocino.cl>"

LABEL traefik.enable="true"
LABEL traefik.http.routers.sumario-backend.entrypoints="sumario"
LABEL traefik.http.routers.sumario-backend.rule="PathPrefix(`/`)"
LABEL traefik.http.routers.sumario-backend.service="sumario-backend@docker"
LABEL traefik.http.routers.sumario-backend.tls="true"
LABEL traefik.http.services.sumario-backend.loadbalancer.server.port="3000"

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

RUN dnf alias add install="\install --setopt=install_weak_deps=False --best"    \
    && rm -f /etc/yum.repos.d/fedora-cisco-openh264.repo

RUN rm -rf /var/cache/{dnf,yum}/*                                               \
    && dnf install -y                                                           \
        dumb-init                                                               \
        git                                                                     \
        make                                                                    \
        nodejs-npm                                                              \
        postgresql                                                              \
        python3-gunicorn                                                        \
        python3-pip                                                             \
    && rm -rf /var/cache/{dnf,yum}/*                                            \
    && dnf clean all

RUN npm install -g uglify-js uglifycss

WORKDIR /mnt/workdir

ENTRYPOINT ["dumb-init", "--"]

CMD ["bash"]
