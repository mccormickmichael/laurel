directory '/opt/thousandleaves' do
  owner 'root'
  group 'root'
  mode '0777'
end

['chef_bootstrap', 'chef_dissociate'].each do |f|
  template "/opt/thousandleaves/#{f}.sh" do
    source "#{f}.erb"
    owner "root"
    group "root"
    mode "0755"
    variables ({
                chef_server_name: node['chef_server_name'],
                chef_server_endpoint: node['chef_server_endpoint'],
                chef_organization: node['chef_organization']
               })
  end
end
