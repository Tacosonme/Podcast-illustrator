#!/bin/bash

# Podcast Illustrator Deployment Script
# This script automates the deployment process

set -e

echo "🎙️ Podcast Illustrator Deployment Script"
echo "========================================="

# Configuration
APP_DIR="/opt/podcast-illustrator"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
UPLOADS_DIR="$APP_DIR/uploads"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python 3.11 is required but not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    # Check FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log_error "FFmpeg is required but not installed"
        exit 1
    fi
    
    # Check pnpm
    if ! command -v pnpm &> /dev/null; then
        log_warn "pnpm not found, installing..."
        npm install -g pnpm
    fi
    
    log_info "All requirements satisfied ✓"
}

# Setup application directories
setup_directories() {
    log_info "Setting up application directories..."
    
    sudo mkdir -p $APP_DIR
    sudo mkdir -p $UPLOADS_DIR
    sudo chown -R $USER:$USER $APP_DIR
    chmod 755 $UPLOADS_DIR
    
    log_info "Directories created ✓"
}

# Deploy backend
deploy_backend() {
    log_info "Deploying backend..."
    
    # Copy backend files
    cp -r podcast-illustrator-backend $BACKEND_DIR
    cd $BACKEND_DIR
    
    # Setup Python environment
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install gunicorn
    
    # Create environment file
    if [ ! -f .env ]; then
        log_warn "Creating .env file - please update with your OpenAI API key"
        cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
FLASK_ENV=production
UPLOAD_FOLDER=$UPLOADS_DIR
EOF
    fi
    
    log_info "Backend deployed ✓"
}

# Deploy frontend
deploy_frontend() {
    log_info "Deploying frontend..."
    
    # Copy frontend files
    cp -r podcast-illustrator-frontend $FRONTEND_DIR
    cd $FRONTEND_DIR
    
    # Install dependencies and build
    pnpm install
    pnpm run build
    
    log_info "Frontend deployed ✓"
}

# Setup systemd service
setup_service() {
    log_info "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/podcast-illustrator-backend.service > /dev/null << EOF
[Unit]
Description=Podcast Illustrator Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/venv/bin
ExecStart=$BACKEND_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 src.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable podcast-illustrator-backend
    
    log_info "Systemd service configured ✓"
}

# Setup Nginx
setup_nginx() {
    log_info "Setting up Nginx..."
    
    # Install Nginx if not present
    if ! command -v nginx &> /dev/null; then
        log_info "Installing Nginx..."
        sudo apt update
        sudo apt install nginx -y
    fi
    
    # Read domain name
    read -p "Enter your domain name (or press Enter for localhost): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        DOMAIN="localhost"
    fi
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/podcast-illustrator > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Frontend static files
    location / {
        root $FRONTEND_DIR/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
    }
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Increase timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Increase max body size for file uploads
        client_max_body_size 100M;
    }
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root $FRONTEND_DIR/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/podcast-illustrator /etc/nginx/sites-enabled/
    sudo nginx -t
    
    log_info "Nginx configured ✓"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start backend
    sudo systemctl start podcast-illustrator-backend
    
    # Start/reload Nginx
    sudo systemctl enable nginx
    sudo systemctl reload nginx
    
    log_info "Services started ✓"
}

# Main deployment flow
main() {
    log_info "Starting Podcast Illustrator deployment..."
    
    check_requirements
    setup_directories
    deploy_backend
    deploy_frontend
    setup_service
    setup_nginx
    start_services
    
    echo ""
    log_info "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update the OpenAI API key in $BACKEND_DIR/.env"
    echo "2. Restart the backend service: sudo systemctl restart podcast-illustrator-backend"
    echo "3. Access your application at: http://$DOMAIN"
    echo ""
    echo "To check service status:"
    echo "  sudo systemctl status podcast-illustrator-backend"
    echo "  sudo systemctl status nginx"
    echo ""
    echo "To view logs:"
    echo "  sudo journalctl -u podcast-illustrator-backend -f"
    echo "  sudo tail -f /var/log/nginx/access.log"
}

# Run main function
main "$@"

