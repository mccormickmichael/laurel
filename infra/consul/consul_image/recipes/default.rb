#
# Cookbook:: consul_image
# Recipe:: default

if node['platform_family'] == 'debian' then
  apt_update
elsif node['platform_family'] == 'amazon' then
  bash 'update_yum' do
    code 'yum update -y'
  end
end

include_recipe 'consul_image::consul_wrapper'
include_recipe 'consul_image::cloudwatch_logs'
