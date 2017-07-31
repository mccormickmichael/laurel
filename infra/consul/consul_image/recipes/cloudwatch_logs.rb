directory '/opt/cwlogs' do
  owner 'root'
  group 'root'
  mode '0755'
  action :create
end

remote_file '/opt/cwlogs/awslogs-agent-setup.py' do
  source 'https://s3.amazonaws.com//aws-cloudwatch/downloads/latest/awslogs-agent-setup.py'
  owner 'root'
  group 'root'
  mode '0755'
  action :create
end

template '/opt/cwlogs/cwlogs.conf' do
  source 'cwlogs.conf'
  owner 'root'
  group 'root'
  mode '0755'
end
