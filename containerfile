# WIP, TESTING ONLY, DO NOT DEPLOY

# Base OS & Dependencies
# FROM python:3.10-slim
#FROM debian:bookworm-slim
FROM registry.arthurvardevanyan.com/apps/analytics-for-spotify:base

ARG quay_expiration=24h
LABEL quay.expires-after=${quay_expiration}

# Setup Analytics For Spotify
COPY . /home/www/analytics-for-spotify/
ADD ./webFrontend/node_modules.tar.xz /home/www/analytics-for-spotify/webFrontend/
RUN chown -R 65534:65534 /home/www/analytics-for-spotify/

# Entry Point
USER 65534
ENTRYPOINT ["/home/www/analytics-for-spotify/container/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
