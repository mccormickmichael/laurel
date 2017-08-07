# file - consul service - (eventually change to template)
# consul itself, download from wherever. Just one version
# dummy config used for test validation only.

directory '/opt/consul' do
  owner 'root'
  group 'root'
  mode '0755'
end

cookbook_file '/etc/init.d/consul' do
  source 'consul.service'
  owner 'root'
  group 'root'
  mode '0755'
end

remote file '/opt/consul/consul' do
  source 'https://releases.hashicorp.com/consul/9.0.0/consul_0.9.0_linux_amd64.zip'
  checksum '33e54c7d9a93a8ce90fc87f74c7f787068b7a62092b7c55a945eea9939e8577f'
  owner 'root'
  group 'root'
  mode '0755'
end

template '/opt/consul/config/config.json' do
  source 'server/test_config.erb'
  owner 'root'
  group 'root'
  mode '0644'
end
