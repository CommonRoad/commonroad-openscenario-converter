FROM continuumio/miniconda3:latest
WORKDIR /home/usr

RUN conda install -y cartopy cython jupyterlab
RUN apt update && apt -y install build-essential git libgl-dev libxrandr-dev libxinerama-dev libfontconfig-dev

COPY commonroad-scenario-designer /deps/commonroad-scenario-designer
RUN pip install -r /deps/commonroad-scenario-designer/requirements.txt && pip install -e /deps/commonroad-scenario-designer

COPY scenariogeneration /deps/scenariogeneration
RUN pip install -e /deps/scenariogeneration

EXPOSE 8888
CMD /opt/conda/bin/jupyter lab --ip='*' --port=8888 --no-browser --allow-root
