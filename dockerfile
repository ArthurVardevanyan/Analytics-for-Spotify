# WIP, TESTING ONLY, DO NOT DEPLOY
FROM python:3.9-slim
RUN apt-get update
RUN apt-get install -y apache2 libapache2-mod-wsgi-py3 libmariadb-dev gcc
COPY . /home/www/analytics-for-spotify/
COPY docker/000-default.conf /etc/apache2/sites-available/000-default.conf
RUN pip3 install -r /home/www/analytics-for-spotify/requirements.txt
ADD ./webFrontend/node_modules.tar.xz /home/www/analytics-for-spotify/webFrontend/
RUN chown -R 10033:10033 /home/www/analytics-for-spotify/
RUN chmod +x /home/www/analytics-for-spotify/docker/startup.sh
RUN echo "ServerName 127.0.0.1" >> /etc/apache2/apache2.conf
RUN echo 'LogFormat "%{%a %b %d %H:%M:%S %Y}t %H %m %U" customLog' >> /etc/apache2/apache2.conf
RUN echo 'ErrorLogFormat "%t %M"' >> /etc/apache2/apache2.conf

COPY docker/ports.conf /etc/apache2/ports.conf
RUN sed -i "s,www-data,www,g" /etc/apache2/envvars


RUN useradd -u 10033 www
RUN chown -R 10033:10033 /var/log/apache2/
RUN chown -R 10033:10033 /var/run/apache2/
RUN chown -R 10033:10033 /proc/self/fd/1
USER 10033

ENTRYPOINT ["/home/www/analytics-for-spotify/docker/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]

EXPOSE 8080
