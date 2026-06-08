

# Jalankan Aplikasi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


# Install NodeJS
curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
sudo yum install -y nodejs

# Install PM2
sudo npm install -g pm2

# Scipt yang sering digunakan PM2
pm2 list
pm2 logs
pm2 restart telegram-listener
pm2 stop telegram-listener
pm2 delete telegram-listener
pm2 monit
pm2 save


# Compile Python ke Binary
python3 -m venv .venv

# Jalankan Program
source .venv/bin/activate
pip install -r requirements.txt

# Jalankan PM2 
pm2 start main.py --name "telegram-listener" --interpreter .venv/bin/python

# Konfigurasi Startup (Auto-start saat VPS restart)
pm2 save
pm2 startup
pm2 logs telegram-listener