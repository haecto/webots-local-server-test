FROM cyberbotics/webots.cloud:R2025a-ubuntu22.04

ARG PROJECT_PATH
ARG MAKE

RUN mkdir -p $PROJECT_PATH

COPY . $PROJECT_PATH

RUN if [ "$MAKE" = "1" ]; then \
      cd $PROJECT_PATH && make; \
    fi

# Create startup script for headless mode
RUN cat > /startup.sh << 'EOF'
#!/bin/bash
export DISPLAY=
export QT_QPA_PLATFORM=offscreen
export WEBOTS_HOME=/usr/local/webots
exec /usr/local/webots/webots --mode=realtime --stdout --stderr "$@"
EOF
RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]
