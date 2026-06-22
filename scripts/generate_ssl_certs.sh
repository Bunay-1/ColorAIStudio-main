#!/bin/bash
# SSL Certificate Generation Script for ICAP
# Generates self-signed certificates for development/testing
# For production, use certificates from a trusted CA

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/../nginx/ssl"
CERT_DAYS=365

echo "Generating SSL certificates for ICAP..."

# Create SSL directory
mkdir -p "$SSL_DIR"

# Generate private key
echo "Generating private key..."
openssl genrsa -out "$SSL_DIR/key.pem" 2048

# Generate certificate signing request
echo "Generating certificate signing request..."
openssl req -new -key "$SSL_DIR/key.pem" -out "$SSL_DIR/csr.pem" -subj "/C=BG/ST=Sofia/L=Sofia/O=ICAP Enterprise/OU=IT/CN=localhost"

# Generate self-signed certificate
echo "Generating self-signed certificate (valid for $CERT_DAYS days)..."
openssl x509 -req -days $CERT_DAYS -in "$SSL_DIR/csr.pem" -signkey "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem"

# Set permissions
chmod 600 "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"

# Clean up CSR
rm "$SSL_DIR/csr.pem"

echo "SSL certificates generated successfully!"
echo "Certificate: $SSL_DIR/cert.pem"
echo "Private Key: $SSL_DIR/key.pem"
echo ""
echo "For production, replace these with certificates from a trusted Certificate Authority."
