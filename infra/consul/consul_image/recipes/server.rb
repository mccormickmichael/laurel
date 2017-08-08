# file - consul service - (eventually change to template)
# consul itself, download from wherever. Just one version
# dummy config used for test validation only.

# include_recipe 'consul_image::packages'
include_recipe 'consul_image::agent'

# Note: Expect this to be overwritten by instances on startup
template '/opt/consul/config/config.json' do
  source 'server/test_config.erb'
  owner 'root'
  group 'root'
  mode '0644'
end

service 'consul' do
  action :start
end
