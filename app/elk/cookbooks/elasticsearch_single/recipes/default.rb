#
# Cookbook Name:: elasticsearch_single
# Recipe:: default
#

apt_update 'Update the apt cache daily' do
  frequency 86_400
  action :periodic
end

package ['curl', 'awscli', 'openjdk-7-jre-headless']

include_recipe 'elasticsearch_single::elasticsearch'
include_recipe 'elasticsearch_single::logstash'
#include_recipe 'elasticsearch_single::kibana'
#include_recipe 'elasticsearch_single::consul_agent'



