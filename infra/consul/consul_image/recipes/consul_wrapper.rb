
# TODO: apply these only when role == server
# TODO: apply other settings when role == client OR role == ui
# node.override[:consul][:config][:server] = true
# node.override[:consul][:config][:bootstrap] = true
# node.override[:consul][:config][:bootstrap_expect] = 3

node.override[:consul][:config][:datacenter] = 'us-west-2'
node.override[:consul][:config][:log_level] = 'INFO'

# These values are replaced by cf-init at boot time
node.rm('consul', 'config', 'bind_addr')
node.rm('consul', 'config', 'retry_join')
# node.override[:consul][:config][:bind_addr] = 'BOGUS'
# node.override[:consul][:config][:retry_join] = 'BOGUS'

include_recipe 'consul::default'

