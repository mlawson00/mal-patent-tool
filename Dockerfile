FROM node:16.14.0 as setup
RUN mkdir apps
RUN mkdir apps/backend
RUN mkdir apps/frontend

RUN apt-get update && \
    apt-get install -y build-essential  && \
    apt-get install -y wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install miniconda
ENV CONDA_DIR /opt/conda

RUN curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh && \
     /bin/bash miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH
RUN conda init bash
SHELL ["/bin/bash", "--login", "-c"]

RUN conda activate
#WORKDIR backend/app
COPY python/apps/backend/conda_env.yaml apps/backend/conda-env.yml
RUN conda env create -f apps/backend/conda-env.yml
RUN conda activate python3
COPY python/apps/backend/backend apps/backend

COPY react/apps/frontend/package.json apps/frontend
COPY react/apps/frontend/nginx.conf /apps/frontend
#WORKDIR frontend/app
COPY react/apps/frontend apps/frontend

FROM setup as dev
WORKDIR apps/frontend
RUN npm install

FROM setup as build
RUN npm run build --prefix apps/frontend

FROM nginx:1.19.4-alpine AS prd
COPY --from=build /apps/frontend/build /usr/share/nginx/html/admin
COPY --from=setup /apps/frontend/nginx.conf /etc/nginx/nginx.conf
## Add Bash to make life easier.
RUN apk add --no-cache bash


FROM setup

COPY --from=prd /usr/share/nginx /usr/share/nginx
COPY --from=prd /etc/nginx /etc/nginx

COPY my_wrapper_script.sh my_wrapper_script.sh
RUN ["chmod", "+x", "my_wrapper_script.sh"]
ENTRYPOINT ["tail", "-f", "/dev/null"]

#CMD ../../my_wrapper_script_0.sh