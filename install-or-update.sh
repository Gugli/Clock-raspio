#!/bin/bash

DIR="$( dirname "${BASH_SOURCE[0]}" )"

if test -z $(which ansible-playbook)
then
	echo "deb http://ppa.launchpad.net/ansible/ansible/uubuntu trusty main" > /etc/apt/sources.list.d/ansible.conf
	apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
	apt-get update
	apt-get --yes install ansible
fi

ansible-playbook 
