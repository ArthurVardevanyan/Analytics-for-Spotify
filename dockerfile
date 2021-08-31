# WIP, TESTING ONLY, DO NOT DEPLOY
FROM python:slim
RUN apt-get update
RUN apt-get install -y apache2 libapache2-mod-wsgi-py3 libmariadb-dev gcc
COPY . /home/root/Analytics-for-Spotify/
COPY docker/000-default.conf /etc/apache2/sites-available/000-default.conf
RUN pip3 install -r /home/root/Analytics-for-Spotify/requirements.txt
ADD ./webFrontend/node_modules.tar.xz /home/root/Analytics-for-Spotify/webFrontend/
RUN chown -R www-data:www-data /home/root/Analytics-for-Spotify/
RUN chmod +x /home/root/Analytics-for-Spotify/docker/startup.sh

ENTRYPOINT ["/home/root/Analytics-for-Spotify/docker/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]

EXPOSE 80
