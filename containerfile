# WIP, TESTING ONLY, DO NOT DEPLOY

# ============================================
# Stage 1: Builder - Install Python packages
# ============================================
FROM registry.arthurvardevanyan.com/apps/analytics-for-spotify:base-builder AS builder

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
	--prefix=/opt/python-packages \
	-r /tmp/requirements.txt

# ============================================
# Stage 2: Runtime - Minimal final image
# ============================================
FROM registry.arthurvardevanyan.com/apps/analytics-for-spotify:base-runtime

ARG quay_expiration=90d
LABEL quay.expires-after=${quay_expiration}

# Copy Python packages from builder (copies lib/ which contains pythonX.X/site-packages)
COPY --from=builder /opt/python-packages/local/lib /usr/local/lib

# Setup Analytics For Spotify
COPY . /home/www/analytics-for-spotify/
RUN chown -R 65534:65534 /home/www/analytics-for-spotify/

# Entry Point
USER 65534
ENTRYPOINT ["/home/www/analytics-for-spotify/container/startup.sh"]
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
