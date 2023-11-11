# Define function directory
ARG FUNCTION_DIR="/function"

# It's python:3.8-alpine3.16
FROM python@sha256:eb2694ea538fff3a9fc66b3e9fdb95ff2db51c8910dfb8881019e30a2393e57a

RUN apk add --no-cache gnupg g++ make cmake unzip curl unixodbc unixodbc-dev autoconf automake libtool libexecinfo-dev git

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Create function directory
RUN mkdir -p ${FUNCTION_DIR}
WORKDIR ${FUNCTION_DIR}

# Create folder for dependencies
ARG DEPENDENCIES_DIR="/dependencies"
RUN mkdir -p ${DEPENDENCIES_DIR}

# Create a group and user
RUN addgroup -S raccoonGang && adduser -S raccoon -G raccoonGang

# make "raccoon" owner of FUNCTION_DIR and DEPENDENCIES_DIR
RUN chown -R raccoon:raccoonGang ${FUNCTION_DIR}
RUN chown -R raccoon:raccoonGang ${DEPENDENCIES_DIR}

# Tell docker that all future commands should run as the "raccoon" user
USER raccoon

# Create function log directory
RUN mkdir -m a=rwx -p ${FUNCTION_DIR}/logs

COPY requirements.txt ${FUNCTION_DIR}/
RUN /usr/local/bin/python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt --target "${DEPENDENCIES_DIR}"

# aws cli doesn't work without this
ENV PATH=$PATH:${FUNCTION_DIR}:${DEPENDENCIES_DIR}:${DEPENDENCIES_DIR}/bin
ENV PYTHONPATH=$PYTHONPATH:${FUNCTION_DIR}:${DEPENDENCIES_DIR}:${DEPENDENCIES_DIR}/bin

COPY --chown=raccoon:raccoonGang market/ ${FUNCTION_DIR}/

ARG version=unknown
RUN echo $version && sed -i "s/##VERSION##/$version/g" market/settings.py

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "market.lambda.handler" ]
