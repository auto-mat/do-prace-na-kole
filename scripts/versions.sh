#!/bin/sh
ansible-playbook -i ./ansible-aws-inventory.yml ansible-playbooks/get_containers.yml --extra-vars "hosts=$1"
