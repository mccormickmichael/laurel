ruby_block 'save node attributes for testing' do
  block do
    if Dir::exist?('/tmp/kitchen')
      IO.write('/tmp/kitchen/chef_node.json', node.to_json)
    end
  end
end
