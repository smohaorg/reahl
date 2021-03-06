FROM ubuntu:20.04 as base

# ---- ENV vars set here are available to all phases of the build going forward

ENV BOOTSTRAP_REAHL_SOURCE=
ENV REAHL_USER=developer
ENV VENV_HOME=/home/$REAHL_USER/.venvs
ENV VENV_NAME=python3.8
ENV BUILD_VENV_NAME=python3.8.build
ENV VENV=$VENV_HOME/$VENV_NAME
ENV BUILD_VENV=$VENV_HOME/$BUILD_VENV_NAME
ENV REAHLWORKSPACE=/home/$REAHL_USER
ENV REAHL_SCRIPTS=$REAHLWORKSPACE/reahl

FROM base as python-install

RUN adduser --disabled-password --gecos '' $REAHL_USER
USER $REAHL_USER

RUN mkdir -p $REAHL_SCRIPTS

COPY --chown=$REAHL_USER:$REAHL_USER ./scripts/installBuildDebs.sh $REAHL_SCRIPTS/scripts/installBuildDebs.sh
COPY --chown=$REAHL_USER:$REAHL_USER ./scripts/installDebs.sh $REAHL_SCRIPTS/scripts/installDebs.sh
COPY --chown=$REAHL_USER:$REAHL_USER ./scripts/installDevEnvDebs.sh $REAHL_SCRIPTS/scripts/installDevEnvDebs.sh

USER root
RUN $REAHL_SCRIPTS/scripts/installBuildDebs.sh && \
    $REAHL_SCRIPTS/scripts/installDebs.sh && \
    $REAHL_SCRIPTS/scripts/installDevEnvDebs.sh

COPY --chown=$REAHL_USER:$REAHL_USER . $REAHLWORKSPACE/reahl


USER $REAHL_USER
RUN $REAHL_SCRIPTS/scripts/createVenv.sh $VENV_NAME
RUN $REAHL_SCRIPTS/scripts/createVenv.sh $BUILD_VENV_NAME

USER root
RUN /etc/init.d/ssh start && \
        sudo -i -u $REAHL_USER -- bash -lex -c "export VENV_NAME=$VENV_NAME; cd $REAHL_SCRIPTS && $REAHL_SCRIPTS/scripts/setupDevEnv.sh" && \
        /etc/init.d/ssh stop

USER $REAHL_USER
RUN mkdir -p $REAHLWORKSPACE/.reahlworkspace/dist-egg
RUN bash -l -c "workon $BUILD_VENV_NAME && cd $REAHL_SCRIPTS && python scripts/bootstrap.py --script-dependencies && python scripts/bootstrap.py --pip-installs; reahl build -sdX; cd reahl-doc/doc; make html"
RUN bash -l -c "workon $VENV_NAME && pip install --pre reahl[all]"

    

FROM base as dev-image
COPY --from=python-install "$REAHL_SCRIPTS/reahl-doc/doc/_build/html" "/usr/share/doc/reahl"

ENV REAHL_SCRIPTS=/opt/reahl
RUN mkdir -p $REAHL_SCRIPTS 

COPY ./scripts $REAHL_SCRIPTS/scripts
COPY ./travis $REAHL_SCRIPTS/travis

RUN $REAHL_SCRIPTS/scripts/installDebs.sh && \
    $REAHL_SCRIPTS/scripts/installDevEnvDebs.sh

RUN adduser --disabled-password --gecos '' $REAHL_USER

COPY --chown=$REAHL_USER:$REAHL_USER --from=python-install "$VENV" "$VENV"

RUN chown $REAHL_USER:$REAHL_USER $VENV_HOME

RUN /etc/init.d/ssh start && \
        sudo -i -u $REAHL_USER -- bash -lex -c "export VENV_NAME=$VENV_NAME; cd $REAHL_SCRIPTS && $REAHL_SCRIPTS/scripts/setupDevEnv.sh" && \
        /etc/init.d/ssh stop

EXPOSE 80 8000 8363
ENTRYPOINT [ "/opt/reahl/scripts/runDevelopmentDocker.sh" ]
CMD [ "/usr/sbin/sshd", "-D" ]


