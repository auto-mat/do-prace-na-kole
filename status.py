#!/usr/bin/python3
import subprocess
import json

instances = json.loads(subprocess.check_output(["aws", "ec2", "describe-instances"]).decode("utf-8"))

states = {
    'terminated': [],
    'running': [],
    'initializing': [],
}
for instance in instances["Reservations"]:
    i = instance["Instances"][0]
    groupName = ""
    try:
        for tag in i["Tags"]:
            if tag["Key"] == "aws:autoscaling:groupName":
                groupName = tag["Value"]
    except KeyError:
        groupName = "no_tags_set"
    state = i["State"]["Name"]
    if state=="terminated":
        states[state].append("%s %s" %(groupName, state))
        continue
    try:
        ip = i["PublicIpAddress"]
        container_listing = subprocess.check_output(["ssh", "-oStrictHostKeyChecking=no", "ubuntu@" + ip, "--", "sudo", "docker", "ps", "--format", "{{.Image}}\ {{.Names}}"]).decode("utf-8")
        container_listing = '\n\t\t'.join(container_listing.splitlines())
    except KeyError:
        ip = "no_ip"
        container_listing = "\n"
    states[state].append("%s %s %s\n\t\t%s" %(groupName, state, ip, container_listing))

for state, instances in states.items():
    print(state)
    for instance in instances:
        print("\t", instance)

