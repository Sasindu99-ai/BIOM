# Deploying to Production
`make build && make collectstatic`
- Convert DEBUG -> RELEASE
- PR to Prod Branch

# Setup Deployment

## 1. Cloudflare Setup
- Add DNS Records
- Add SSL Certificate

## 2. Adding SSL Certificate & Key to the Server
- Navigate to /etc/nginx/ssl/cloudflare/
`cd /etc/nginx/ssl/cloudflare/`
`sudo nano biom.crt`
`sudo nano biom.key`
- Add SSL Certificate & Key
- Restart Nginx
`sudo systemctl restart nginx` or Restart using aaPanel

## 3. Adding SSH Key to GitHub
- Run this command on your local machine
- Generate SSH Key
`ssh-keygen -t ed25519 -b 4096 -C "[EMAIL_ADDRESS]" -f ~/.ssh/biom`
- Copy SSH Key
`cat ~/.ssh/biom.pub`
- Add SSH Key to GitHub
- Navigate to https://github.com/settings/keys
- Add SSH Key to GitHub Repo Secerts: SSH_PRIVATE_KEY
`cat ~/.ssh/biom`
- Add Host server Ip to GitHub Repo Secerts: SSH_HOST
- Add Host server user ( root ) to Github Repo Secrets: SSH_USER

## 4. Server Setup
- Create Directory
`sudo mkdir -p /var/www/biom/{staticfiles,media,logs,repo}`
`sudo chown -R $USER:$USER /var/www/biom`
- Clone Repository
`cd /var/www/biom/repo`
`git clone git@github.com:Sasindu99-ai/BIOM.git BIOM`
`git checkout prod`
- Create .env File
`sudo nano /var/www/biom/repo/BIOM/.env`

## 5. Nginx Configuration
- Create Nginx Configuration
`sudo nano /www/server/panel/vhost/nginx/biom.arceion.com.conf`
- Add `nginx/yourdomain.conf` to the file
- Restart Nginx
`sudo systemctl restart nginx` or Restart using aaPanel

## 6. PostgreSQL Configuration
- Create a Database using aaPanel
- Add configuration to .env file

## 7. Django Secure Setup
- Generate a secure secret key
`python -c "import secrets; print(secrets.token_urlsafe(50))"`
- Add configuration to .env file

## 8. PR to Prod Branch
`make build && make collectstatic`
- Convert DEBUG -> RELEASE
- PR to Prod Branch

## 9. Expose Port
- Expose port 8001
`sudo ufw allow 8001`

# Troubleshooting
- Check Docker Logs
`docker logs biom_app`
- Check ufw status
`sudo ufw status`
- Check Docker Status
`docker ps`
