git add .
git commit -m "changes"
git push origin main

ssh -i /Users/khurelsukh/Projects/aws/FindNBite-key-pair.pem ubuntu@3.149.240.248

cd findnbite-backend
git pull

# Start server & check status
pm2 stop all
pm2 start server.js
pm2 list
pm2 restart all
pm2 logs


rm -rf node_modules package-lock.json
npm install
kill -9 $(lsof -t -i:3000)