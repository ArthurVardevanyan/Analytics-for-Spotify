# WIP, TESTING ONLY, DO NOT DEPLOY

# Base OS & Dependencies
FROM registry.arthurvardevanyan.com/apps/analytics-for-spotify:base

ARG quay_expiration=90d
LABEL quay.expires-after=${quay_expiration}

# Setup Analytics For Spotify
COPY . /home/www/analytics-for-spotify/
RUN chown -R 65534:65534 /home/www/analytics-for-spotify/

RUN cd /home/www/analytics-for-spotify/ && \
	python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

# Entry Point
USER 65534
ENTRYPOINT ["/home/www/analytics-for-spotify/container/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
