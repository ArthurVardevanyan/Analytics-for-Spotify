# WIP, TESTING ONLY, DO NOT DEPLOY
FROM debian
ENV PYTHONUNBUFFERED=1
run apt-get update
run apt-get install -y apache2 libapache2-mod-wsgi-py3 libmariadb-dev python3 python3-pip
COPY . /home/root/Analytics-for-Spotify/
COPY docker/000-default.conf /etc/apache2/sites-available/000-default.conf
RUN pip3 install -r /home/root/Analytics-for-Spotify/requirements.txt
add ./webFrontend/node_modules.tar.xz /home/root/Analytics-for-Spotify/webFrontend/
run chown -R www-data:www-data /home/root/Analytics-for-Spotify/

CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]

EXPOSE 80
