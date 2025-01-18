git add .
git commit -m "changes"
git push origin master

ssh -i /Users/khurelsukh/Projects/aws/FindNBite-key-pair.pem ubuntu@3.149.240.248

cd findnbite-backend
git pull

# Start server & check status
source venv/bin/activate
sudo systemctl stop flask-app
sudo systemctl start flask-app
sudo systemctl enable flask-app