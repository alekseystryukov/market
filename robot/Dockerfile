FROM ppodgorsek/robot-framework:latest

USER root

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY bin/get_env.py /opt/robotframework/bin/get_env.py
COPY bin/post_run.py /opt/robotframework/bin/post_run.py
RUN chmod +x /opt/robotframework/bin/get_env.py
RUN chmod +x /opt/robotframework/bin/post_run.py

USER ${ROBOT_UID}:${ROBOT_GID}


COPY tests  /opt/robotframework/tests

CMD ["sh","-c", "get_env.py && set -a && . /tmp/.env && set +a && run-tests-in-virtual-screen.sh || true && post_run.py"]
