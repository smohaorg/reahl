#!/bin/sh -evx

if [ ! -f /.provisioned ]; then
    # Regenerate host keys
    /bin/rm -fv /etc/ssh/ssh_host_*
    dpkg-reconfigure openssh-server

    # Secure ssh (we modify its config here after the reconfigure above to avoid it asking about changes to config files)
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "ClientAliveInterval 30" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "AddressFamily inet" >> /etc/ssh/sshd_config.d/reahl.conf  # For ssh X11 forwarding to work
    
    # Fake /run/user/1000
    mkdir -p /run/user/1000
    chown $REAHL_USER.$REAHL_USER /run/user/1000
    chmod 700 /run/user/1000
    
    /etc/init.d/ssh start

    # Update localhost known_hosts
    su $REAHL_USER -c -- bash -l -c 'ssh-keyscan -t rsa localhost > ~/.ssh/known_hosts'

    if [ ! -z "$BOOTSTRAP_REAHL_SOURCE" ]; then
        $REAHL_SCRIPTS/scripts/installBuildDebs.sh
        su $REAHL_USER -c -- bash -l -c "
           deactivate
           rmvirtualenv $VENV_NAME
           $REAHL_SCRIPTS/scripts/createVenv.sh $VENV_NAME
           workon $VENV_NAME
           cd $BOOTSTRAP_REAHL_SOURCE
           python3 scripts/bootstrap.py --script-dependencies
           python3 scripts/bootstrap.py --pip-installs
        "
    fi

    /etc/init.d/ssh stop

    touch /.provisioned
fi

