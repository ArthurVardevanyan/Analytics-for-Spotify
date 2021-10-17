# WIP, TESTING ONLY, DO NOT DEPLOY
FROM python:3.9-slim
RUN apt-get update
RUN apt-get install -y apache2 libapache2-mod-wsgi-py3 libmariadb-dev gcc
COPY . /home/root/analytics-for-spotify/
COPY docker/000-default.conf /etc/apache2/sites-available/000-default.conf
RUN pip3 install -r /home/root/analytics-for-spotify/requirements.txt
ADD ./webFrontend/node_modules.tar.xz /home/root/analytics-for-spotify/webFrontend/
RUN chown -R www-data:www-data /home/root/analytics-for-spotify/
RUN chmod +x /home/root/analytics-for-spotify/docker/startup.sh
RUN echo "ServerName 127.0.0.1" >> /etc/apache2/apache2.conf
RUN echo 'LogFormat "%{%a %b %d %H:%M:%S %Y}t %H %m %U" customLog' >> /etc/apache2/apache2.conf
RUN echo 'ErrorLogFormat "%t %M"' >> /etc/apache2/apache2.conf

ENTRYPOINT ["/home/root/analytics-for-spotify/docker/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]

EXPOSE 80
