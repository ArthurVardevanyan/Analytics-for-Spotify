# WIP, TESTING ONLY, DO NOT DEPLOY

# Base OS & Dependencies
# FROM python:3.9-slim
FROM registry.arthurvardevanyan.com/apps/analytics-for-spotify:base

ARG quay_expiration=24h
LABEL quay.expires-after=${quay_expiration}

RUN apt-get update && apt-get install -y apache2 libapache2-mod-wsgi-py3 libmariadb-dev gcc && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Custom Apache Logs
RUN echo 'LogFormat "%{%a %b %d %H:%M:%S %Y}t %H %m %U" customLog' >> /etc/apache2/apache2.conf
RUN echo 'ErrorLogFormat "%t %M"' >> /etc/apache2/apache2.conf

# Supress Apache Server Name Error
RUN echo "ServerName 127.0.0.1" >> /etc/apache2/apache2.conf

# Required Read Only Root File System
RUN sed -i "s,ErrorLog \${APACHE_LOG_DIR}/error.log,ErrorLog /proc/self/fd/1,g" /etc/apache2/apache2.conf
RUN sed -i "s,CustomLog \${APACHE_LOG_DIR}/other_vhosts_access.log,CustomLog /proc/self/fd/1,g" /etc/apache2/conf-available/other-vhosts-access-log.conf
RUN sed -i "s,/var/run/apache2\$SUFFIX/,/dev/shm/,g" /etc/apache2/envvars
RUN sed -i "s,/var/run/apache2\$SUFFIX,/dev/shm/apache2\$SUFFIX,g" /etc/apache2/envvars
RUN sed -i "s,#WSGISocketPrefix /var/run/apache2/,WSGISocketPrefix /dev/shm/apache2/,g" /etc/apache2/mods-available/wsgi.conf

# Ports
EXPOSE 8080
COPY container/000-default.conf /etc/apache2/sites-available/000-default.conf
RUN sed -i "s,80,8080,g" /etc/apache2/ports.conf

# Non Root User Settings
RUN sed -i "s,www-data,www,g" /etc/apache2/envvars
RUN useradd -u 10033 www
RUN chown -R 10033:10033 /var/log/apache2/
RUN chown -R 10033:10033 /var/run/apache2/
RUN chown -R 10033:10033 /proc/self/fd/1

# Setup Python
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Setup Analytics For Spotify
COPY . /home/www/analytics-for-spotify/
ADD ./webFrontend/node_modules.tar.xz /home/www/analytics-for-spotify/webFrontend/
RUN chown -R 10033:10033 /home/www/analytics-for-spotify/

# Entry Point
USER 10033
ENTRYPOINT ["/home/www/analytics-for-spotify/container/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
