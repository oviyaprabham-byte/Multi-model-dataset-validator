#!/usr/bin/env bash
# Render build script — builds frontend then installs backend deps

set -e

echo ">>> Building frontend..."
cd frontend
npm install
npm run build
echo ">>> Frontend built."

echo ">>> Copying dist to backend/static..."
cd ..
rm -rf backend/static
cp -r frontend/dist backend/static
echo ">>> Done copying."

echo ">>> Installing backend dependencies..."
cd backend
pip install -r requirements.txt
echo ">>> Backend ready."
