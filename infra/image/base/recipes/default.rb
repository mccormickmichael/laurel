['/etc/chef', '/var/lib/chef', '/var/log/chef'].each do |dir|
  directory dir do
    owner 'root'
    group 'root'
    mode '0755'
  end
end

# TODO: install aws cli if not already there
# TODO: how to set user access keys? hopefully copy them from my ~/.aws/credentials file
# TODO: copy infra-validator.pem from S3

# For now, copy it from a local location
validator_key_path = "/etc/chef/#{node['chef']['org']['validator']}.pem"
cookbook_file validator_key_path do
  source 'temp-validator.pem'
  owner 'root'
  group 'root'
  mode '0755'
end

remote_file '/tmp/chef_omnitruck_installer' do
  source 'https://omnitruck.chef.io/install.sh'
  owner 'root'
  group 'root'
  mode '0755'
  notifies :run, 'execute[install_chef_client]', :immediately
end

# Not sure about this one, is it already there by virtue of the fact that we are using chef in the first place?
execute 'install_chef_client' do
  cwd '/etc/chef'
  command "/tmp/chef_omnitruck_installer"
  action :nothing
end

cookbook_file '/etc/chef/first-boot.json' do
  source 'first-boot.json'
  owner 'root'
  group 'root'
  mode '0644'
end

node_name = "test-kitchen-base-image-#{Random.rand(1000).to_s(16)}"

template '/etc/chef/client.rb' do
  source 'client.erb'
  owner 'root'
  group 'root'
  mode '0644'
  variables({
             chef_server_url: node['chef']['server'],
             validator_key: node['chef']['org']['validator'],
             validator_key_path: validator_key_path,
             this_node_name: node_name
            })
end
