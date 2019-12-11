#!/usr/bin/python3
import aws_dpnk
import yaml

inventories, states = aws_dpnk.get_inventories()
with open('ansible-aws-inventory.yml', 'w') as fd:
    fd.write(yaml.dump(inventories, default_flow_style=False))

for state, instances in states.items():
    print(state)
    for instance in instances:
        print("\t", "%s %s %s %s %s" % instance)
