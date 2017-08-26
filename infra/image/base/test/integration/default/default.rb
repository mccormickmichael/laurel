describe directory('/opt/thousandleaves') do
  it { should exist }
end

['chef_bootstrap', 'chef_dissociate'].each do |f|
  describe file("/opt/thousandleaves/#{f}.sh") do
    it { should exist }
    its('content') { should match(%r{CHEF_ORGANIZATION="anthrax"}) }
    its('content') { should match(%r{CHEF_SERVER_NAME="test-chef-server-name"}) }
    its('content') { should match(%r{CHEF_SERVER_ENDPOINT="https://test-chef-server-endpoint.io"}) }
  end
end
