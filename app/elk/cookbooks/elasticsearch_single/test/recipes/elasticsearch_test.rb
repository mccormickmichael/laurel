# # encoding: utf-8

# Inspec test for recipe elasticsearch_single::elasticsearch

# The Inspec reference, with examples and extensive documentation, can be
# found at https://docs.chef.io/inspec_reference.html


describe package 'elasticsearch' do
  it {should be_installed }
end
describe service 'elasticsearch' do
  it { should be_installed }
  it { should be_enabled }
  it { should be_running }
end

# Elasticsearch abuses yaml syntax by using dotted names. Use file content matching instead
describe file('/etc/elasticsearch/elasticsearch.yml') do
  its('content') { should match(/cluster\.name:[[:blank:]]+laurel-tiny/) }
end

# Is there a better way to visit a url?
# And then inspect the result as json?
describe command("curl -XGET 'localhost:9200/_cluster/health'") do
  its('stdout') { should match (/"status":"green"/) }
end
