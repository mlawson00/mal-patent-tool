FROM continuumio/anaconda3 as python_image

COPY conda_env.yaml conda-env.yaml
RUN conda init bash
SHELL ["/bin/bash", "--login", "-c"]
RUN conda env create -f conda-env.yaml
# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "python3", "/bin/bash", "-c"]


COPY main.py main.py
COPY inference_model.py inference_model.py
#ENTRYPOINT ["tail", "-f", "/dev/null"]
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "python3", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
