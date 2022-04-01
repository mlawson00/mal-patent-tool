#!/bin/bash --login
#/bin/bash -ic "source ~/.bashrc"
conda activate python3
# Start the first process
echo "about the run uvicorn $(conda list)"
cd ../../backend
echo "about the run uvicorn changed directory $(ls)"
uvicorn app.main:app --host 0.0.0.0:8000 --reload
uvicorn backend.backend.main:app --host 0.0.0.0:8000 --reload
# Start the second process
#cd ../../frontend/app & npm start

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?