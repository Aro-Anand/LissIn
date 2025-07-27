#!/bin/bash
# Launch main.py in the background
python main.py start &
# Wait for 10 seconds
sleep 10
# Run app.py in the foreground
python app.py