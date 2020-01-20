import collections
import json
import yaml
import subprocess

def get_inventories():
    instances = json.loads(subprocess.check_output(["aws", "ec2", "describe-instances"]).decode("utf-8"))

    ########### ELBs ##########################
    elb_prod_arn = 'arn:aws:elasticloadbalancing:eu-west-1:930821752279:targetgroup/dpnk/67c4d6e00abf2f57'
    elb_test_arn = 'arn:aws:elasticloadbalancing:eu-west-1:930821752279:targetgroup/dpnk-test/4a530ccfaf7ade97'
    def get_targets(elb):
        return json.loads(subprocess.check_output(['aws', 'elbv2', 'describe-target-health', '--target-group-arn', elb,  '--query', 'TargetHealthDescriptions[*].Target.Id']).decode("utf-8"))
    elb_prod = get_targets(elb_prod_arn)
    elb_test = get_targets(elb_test_arn)
    instance_elbs = {}
    for instance in elb_prod:
        instance_elbs[instance] = "elb_prod"

    for instance in elb_test:
        instance_elbs[instance] = "elb_test"
    ##########################

    states = collections.OrderedDict([
        ('terminated', []),
        ('stopped', []),
        ('pending', []),
        ('initializing', []),
        ('running', []),
        ('shutting-down', []),
    ])

    inventories = {}

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
        if state == "terminated":
            states[state].append(
                (groupName, state, '', '', ''),
            )
            continue
        try:
            ip = i["PublicIpAddress"]
            inventories[groupName] = inventories.get(groupName, {})
            inventories[groupName]["hosts"] = inventories[groupName].get("hosts", {})
            inventories[groupName]["hosts"][ip] = {"ansible_host": ip, "ansible_user": "ubuntu"}
        except KeyError:
            ip = "no_ip"
        states[state].append(
            (
                groupName,
                state,
                ip,
                i["InstanceId"],
                instance_elbs.get(i['InstanceId'], 'unregistered'),
            ),
        )
    return inventories, states
