#!/bin/bash

ANSIBLE_VERSION="stable-2.4"
DIR="$( dirname "${BASH_SOURCE[0]}" )"

apt-get update
apt-get install git
mkdir "$DIR/tmp/"
git clone "https://github.com/ansible/ansible.git" "$DIR/tmp/ansible"
git switch "$DIR/tmp/ansible" $ANSIBLE_VERSION