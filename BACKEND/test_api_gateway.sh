#!/bin/bash

echo "Testing API Gateway on port 8090"

echo -e "\nTesting Auth Service"
curl -i http://localhost:8090/auth/

echo -e "\nTesting Admin Service"
curl -i http://localhost:8090/admin/

echo -e "\nTesting Chatbot Service"
curl -i http://localhost:8090/chat/

echo -e "\nTesting Preprocess Service"
curl -i http://localhost:8090/preprocess/

echo -e "\nTesting ML Service"
curl -i http://localhost:8090/ml/

echo -e "\nTesting Default Route (Chatbot)"
curl -i http://localhost:8090/ 