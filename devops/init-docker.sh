#!/bin/bash
# init script for docker ssh instance
# enable ssh into a server as $RUN_USER via authorized keys
# 
# Adds RUN_USER and adds AUTHORIZED_KEYS for that user if vars are set

function add_auth_keys {
    local auth_keys="$1"
    local auth_user="$2"
    
    local ssh_dir=/home/$auth_user/.ssh
    if [[ $auth_user == "root" ]]; then
        ssh_dir=/root/.ssh
    fi

    echo "=> Adding authorized keys $auth_keys for $auth_user"
    mkdir -p $ssh_dir
    chmod 700 $ssh_dir 
    touch $ssh_dir/authorized_keys
    chmod 600 $ssh_dir/authorized_keys
    chown -R $auth_user:$auth_user $ssh_dir
    IFS=$'\n'
    arr=$(echo ${auth_keys} | tr "," "\n")
    for x in $arr
    do
        x=$(echo $x | sed -e 's/^ *//' -e 's/ *$//')
        cat $ssh_dir/authorized_keys | grep "$x" >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "=> Adding public key to .ssh/authorized_keys: $x"
            echo "$x" >> $ssh_dir/authorized_keys
        fi
    done
}

if [ ${RUN_USER} ]; then
    echo "=> Adding user $RUN_USER"
    useradd -s /bin/bash -m -G sudo $RUN_USER 
fi
 
# setup authorized keys for ssh access
if [ "${AUTHORIZED_KEYS}" ]; then
    add_auth_keys "${AUTHORIZED_KEYS}" "${RUN_USER}"
    # NOTE:  Adding to root as well
    add_auth_keys "${AUTHORIZED_KEYS}" root
fi

# run ssh 
/usr/sbin/sshd -D
