include_recipe 'consul_image::packages'

['/opt/consul', '/opt/consul/config', '/var/lib/consul'].each do |dir|
  directory dir do
    owner 'root'
    group 'root'
    mode '0755'
  end
end

consul_version = node['consul']['agent']['version']

remote_file "/opt/consul/consul_#{consul_version}.zip" do
  source "https://releases.hashicorp.com/consul/#{consul_version}/consul_#{consul_version}_linux_amd64.zip"
  checksum "#{node['consul']['agent']['checksum']}"
  owner 'root'
  group 'root'
  mode '0755'
  notifies :run, 'execute[extract_consul]', :immediately
end

execute 'extract_consul' do
  cwd '/opt/consul'
  command "unzip -o consul_#{consul_version}.zip"
  action :nothing
end

if node['platform_family'] == 'debian' then
  cookbook_file '/etc/systemd/system/consul.service' do
    source 'consul.systemd'
    owner 'root'
    group 'root'
    mode '0644'
  end
elsif node['platform_family'] == 'amazon' then
  cookbook_file '/etc/init.d/consul' do
    source 'consul.service'
    owner 'root'
    group 'root'
    mode '0755'
  end
end

directory '/opt/consul/config' do
  owner 'root'
  group 'root'
  mode '0755'
end

service 'consul' do
  action [:enable]
end

