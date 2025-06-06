def get_port_mappings(pod_stat: dict):
    """
    Extract all port mappings from pod statistics dictionary.

    Args:
        pod_stat (dict): Dictionary containing pod statistics including runtime information

    Returns:
        dict: A dictionary containing different service connections:
            {
                'ssh': {'ip': str, 'port': int},
                'http': {'ip': str, 'port': int},
                'custom': [{'ip': str, 'private_port': int, 'public_port': int, 'type': str}]
            }

    Raises:
        KeyError: If required keys are missing from the dictionary
    """
    try:
        if 'runtime' not in pod_stat or 'ports' not in pod_stat['runtime']:
            raise KeyError("Pod statistics missing runtime ports information")

        result = {
            'ssh': None,
            'http': None,
        }

        for port_config in pod_stat['runtime']['ports']:
            if not port_config.get('isIpPublic'):
                continue

            ip = port_config['ip']
            private_port = port_config['privatePort']
            public_port = port_config['publicPort']

            # SSH configuration (port 22)
            if private_port == 22 and port_config['type'] == 'tcp':
                result['ssh'] = {
                    'ip': ip,
                    'port': public_port
                }

            # HTTP server (port 9000)
            elif private_port == 9000 and port_config['type'] == 'tcp':
                result['http'] = {
                    'ip': ip,
                    'port': public_port
                }

            # Any other ports
            else:
                result['custom'].append({
                    'ip': ip,
                    'private_port': private_port,
                    'public_port': public_port,
                    'type': port_config['type']
                })

        return result

    except KeyError as e:
        raise KeyError(f"Failed to extract port mappings: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing pod statistics: {str(e)}")