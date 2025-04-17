FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wireguard \
    iptables \
    systemd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install flask

# Create necessary directories
RUN mkdir -p /etc/wireguard

# Copy the application code
COPY wg_helper.py /app/wg_helper.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 5050 51820/udp

# Set working directory
WORKDIR /app

# Start the application
CMD ["python3", "wg_helper.py"] 