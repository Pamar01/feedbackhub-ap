#!/usr/bin/env bash
# Run this from inside the feedbackhub folder on your own computer.
# 1) Create an EMPTY repo named "feedbackhub-api" on GitHub (no README) under your account Pamar01.
# 2) Then run: bash push_to_github.sh
set -e
git init -b main
git add .
git commit -m "Add FeedbackHub: feedback collection REST API with sentiment analytics"
git remote add origin https://github.com/Pamar01/feedbackhub-api.git
git push -u origin main
