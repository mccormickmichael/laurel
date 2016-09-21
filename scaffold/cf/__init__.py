#!/usr/bin/python

def assume_role_policy_document(service):
    return {
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': [service]},
            'Action': ['sts:AssumeRole']
        }]
    }

assume_role_policy_document.ec2 = assume_role_policy_document('ec2.amazonaws.com')
assume_role_policy_document.opsworks = assume_role_policy_document('opsworks.amazonaws.com')

                        
