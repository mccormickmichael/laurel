import yaml

with open('es-tiny.yml', 'r') as f:
    es_config = yaml.load(f)

# this magic file is written out by our userdata script
with open('/tmp/es_network_host', 'r') as f:
    network_host = f.read().strip().strip('"')

es_config['network']['host'] = network_host

with open('elasticsearch.yml', 'w') as f:
    yaml.dump(es_config, f, default_flow_style=False)
