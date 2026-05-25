# Smart Retail Shelf Monitoring System

An AI-powered retail shelf monitoring system that detects products and monitors shelf activity using Computer Vision and Deep Learning techniques.

## 🚀 Project Overview

This project is designed to automate retail shelf monitoring using object detection models. The system helps retailers track product availability, detect missing items, and improve inventory management efficiency.

The application uses a backend API, machine learning models, and Dockerized deployment for scalable execution.

---

## ✨ Features

- Real-time object detection
- Retail shelf monitoring
- AI/ML-based product identification
- Dockerized deployment
- REST API integration
- S3 image upload support
- Backend service integration
- Scalable project structure

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI

### Machine Learning
- YOLOv8
- OpenCV

### Database
- MongoDB

### DevOps / Deployment
- Docker
- Docker Compose

### Cloud
- AWS S3

---

## 📂 Project Structure

```bash
retail-shelf/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   └── s3_uploader.py
│
├── dashboard/
├── model/
├── data/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md