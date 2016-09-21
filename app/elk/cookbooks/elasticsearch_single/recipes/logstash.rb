#
# Cookbook Name:: elasticsearch_single
# Recipe:: logstash
#

# https://download.elastic.co/logstash/logstash/packages/debian/logstash-2.4.0_all.deb
# or pull from S3

cookbook_file '/tmp/logstash-2.4.0.deb' do
  source 'https://download.elastic.co/logstash/logstash/packages/debian/logstash-2.4.0_all.deb'
end

dpkg_package 'logstash' do 
  source '/tmp/logstash-2.4.0.deb'
end

template '/etc/logstash/conf.d/logstash.conf' do
  source 'logstash_tiny.erb'
  mode '0755'
  owner 'logstash'
  group 'logstash'
end  


service 'logstash' do
  action [:start, :enable]
  supports :restart => true, :reload => true, :status => true
end
