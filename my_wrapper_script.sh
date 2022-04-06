#/bin/bash -ic "source ~/.bashrc"
#!/bin/bash --login
conda activate python3
# Start the first process
echo "about the run uvicorn $(conda list)"
#go into the "apps" folder to run uvicorn due to the way the project was set up
cd ..
echo "about the run uvicorn changed directory $(ls)"
uvicorn backend.main:app & npm start --prefix frontend
# Start the second process
# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?