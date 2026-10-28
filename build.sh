#!/usr/bin/env bash
# Render build script — builds frontend then installs backend deps

set -e

echo ">>> Building frontend..."
cd frontend
npm install
npm run build:render
echo ">>> Frontend built."

echo ">>> Checking dist was created..."
if [ ! -d "dist" ]; then
  echo "ERROR: frontend/dist not found after build!"
  exit 1
fi

echo ">>> Copying dist to backend/static..."
cd ..
rm -rf backend/static
cp -r frontend/dist backend/static
echo ">>> Done copying. Contents:"
ls -la backend/static/

echo ">>> Installing backend dependencies..."
cd backend
pip install -r requirements.txt
echo ">>> Backend ready."
