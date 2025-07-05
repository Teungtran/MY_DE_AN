#!/bin/bash

echo "Testing API Gateway on port 8888"

echo -e "\nTesting Auth Service"
curl -i http://localhost:8888/auth/

echo -e "\nTesting Admin Service"
curl -i http://localhost:8888/admin/

echo -e "\nTesting Chatbot Service"
curl -i http://localhost:8888/chat/

echo -e "\nTesting Preprocess Service"
curl -i http://localhost:8888/preprocess/

echo -e "\nTesting ML Service"
curl -i http://localhost:8888/ml/

echo -e "\nTesting Default Route (Chatbot)"
curl -i http://localhost:8888/fe/