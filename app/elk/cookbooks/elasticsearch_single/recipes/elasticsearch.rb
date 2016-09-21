#
# Cookbook Name:: elasticsearch_single
# Recipe:: elasticsearch
#
# Provision a single-node elastic search cluster

# TODO: when building on an AWS resource, change this to pull from S3
cookbook_file '/tmp/elasticsearch-2.4.0.deb' do
  source 'https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.0/elasticsearch-2.4.0.deb'
end

dpkg_package 'elasticsearch' do 
  source '/tmp/elasticsearch-2.4.0.deb'
end

template '/etc/elasticsearch/elasticsearch.yml' do
  source 'es_config_tiny.erb'
  mode '0755'
  owner 'elasticsearch'
  group 'elasticsearch'
  # This breaks veficiation if it's run immediately after (e.g. kitchen test) WHY?
  # verification works fine after a couple of seconds
  # notifies :restart, 'service[elasticsearch]', :delayed
end

service 'elasticsearch' do
  action [:start, :enable]
  supports :restart => true, :reload => false, :status => true
end

# configure Elasticsearch via /etc/elasticsearch/elasticsearch.yml
# cluster.name = laurel-tiny
# node.max_local_storage_nodes: 1
