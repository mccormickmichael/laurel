if node['platform_family'] == 'debian' then
  apt_update
elsif node['platform_family'] == 'amazon' then
  bash 'update_yum' do
    code 'yum update -y'
  end
end

package 'unzip' do
  package_name 'unzip'
end
