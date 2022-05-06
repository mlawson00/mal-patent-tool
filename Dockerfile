
FROM continuumio/anaconda3 as python_build

RUN apt-get update && apt-get install -y nginx  && apt-get clean

RUN mkdir apps
RUN mkdir /apps/backend
RUN mkdir /apps/frontend

COPY python/apps/backend/conda-env.yaml apps/backend/conda-env.yaml
RUN conda init bash
SHELL ["/bin/bash", "--login", "-c"]
RUN conda env create -f apps/backend/conda-env.yaml
RUN conda activate python3



FROM node:16.14.0 as node_setup
RUN mkdir apps
RUN mkdir apps/frontend
COPY react/apps/frontend apps/frontend

WORKDIR apps/frontend
RUN npm install
RUN npm run build

FROM python_build as final_image

COPY --from=node_setup /apps/frontend/build /usr/share/nginx/html/admin
COPY python/apps/backend/backend apps/backend
COPY my_wrapper_script.sh my_wrapper_script.sh
RUN ["chmod", "+x", "my_wrapper_script.sh"]
COPY nginx.conf /etc/nginx/nginx.conf
CMD ./my_wrapper_script.sh
#ENTRYPOINT ["tail", "-f", "/dev/null"]