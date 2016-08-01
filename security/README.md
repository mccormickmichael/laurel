# IAM Security in Laurel

The job `update_iam` will synchronize an account's users, groups, roles, and policies with those defined in the set of files described below.

## Usage

Required arguments:

+ `basedir` - path to the directory containing the users, groups, roles and policy files.

Optional arguments:

+ `--iam-stack` - If you have policies defined in a CloudFormation stack, the script will inspect this stack's outputs for policies and will include them when resolving policy names.
+ `--profile` - The name of the aws credentials profile to use. Defaults to 'default'.
+ `--region` - The region to connect to. Required if using a profile other than 'default'.
+ `--dry-run` - Do not perform any mutable actions, like creating, deleting, or updating elements. (This may cause the job to fail if policies or groups should be created)

## File and directory structure

The directory passed to the job should have these files and directory:

+ `users.yml` - This file describes users and the groups to which they belong.
+ `groups.yml` - This file describes groups and the policies assigned to each group.
+ `roles.yml` - This file describes roles and the policies assigned to each role. Both service roles and user-assumable roles are defined here.
+ `policies/` - This directory contains policies used by groups and roles. One policy per file. The name of the file becomes the policy name.

### users.yml

This example defines two human users, both belonging to the `Developers` group. Each of the humans also belongs to another group. The file also defines a machine user (in this case, used by travis-ci)

```yml
alice:
  - InfrastructureDevelopers
  - Developers

bob:
  - WebsiteDevelopers
  - Developers

machine-travis:
  - MachinePublisher
```

### groups.yml

This example defines groups mentioned in the users.yml file, and the policies assigned to each of those groups. Both Amazon-defined and account-defined policies can be specified here. In addition, policies built in CloudFormation can be specified here. Use the Name from the stack's Output section.

```yml
Developers:
  - user-manage-iam-keys
  - ReadOnlyAccess

WebsiteDevelopers:
  - AmazonS3FullAccess
  - AmazonRoute53FullAccess

InfrastructureDevelopers:
  - user-manage-cloudformation-stacks

MachinePublisher:
  - machine-deploy-s3
```

### roles.yml

This example defines a role assumable by a user, a role assumable by an ec2 instance, and a role assumable by an external account role.

```yml
Sudoer:
  Principal:
    users:
      - alice
      - bob
  Policies:
    - AdministratorAccess
  InstanceProfile: False

WebPortal:
  Principal:
    Service: ec2.amazonaws.com
  Policies:
    - AmazonDynamoDBReadOnlyAccess
  InstanceProfile: True

CrossAccountAuditor:
  Principal
    AWS: arn:aws:iam::123456789012:role/auditor
  Policies:
    - ReadOnlyAccess
```

#### Principal

This element defines the Principals that may assume this role. There are two special cases:

+ `users`: This defines a list of users in the current account that may assume the role, as seen in the example.
+ `roles`: This defines a list of other roles in the current account that may assume the role.

Otherwise, the Principal element reflects the Principal element of the assume-role policy document.

#### Policies

This element specifies the list of policies that should be assigned to the role.

#### InstanceProfile

If this element exists and is True, an instance profile will be created along with the role, allowing ec2 instances to adopt the role. If the element is omitted or is False no instance profile is created.

The example above will produce the following assume-role policy documents:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::987654321098:user/alice", "arn:aws:iam::987654321098:user/bob"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/auditor"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### policies/

This directory should contain a set of policy documents, one policy per file. The name of the file becomes the name of the policy. See the `policies` directory for examples.