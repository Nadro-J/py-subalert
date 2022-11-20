from pathlib import Path

file = Path(__file__).resolve()
package_root_directory = file.parents[1]

import yaml
from substrateinterface import SubstrateInterface
import ssl


class Configuration:
    def __init__(self):
        self.yaml_file = yaml.safe_load(open(f"{package_root_directory}/config.local.yaml", "r"))
        self.sslopt = {"cert_reqs": ssl.CERT_NONE}
        self.substrate = SubstrateInterface(
            url=self.yaml_file['chain']['url'],
            ss58_format=self.yaml_file['chain']['ss58_format'],
            type_registry_preset=self.yaml_file['chain']['type_registry_preset'],
            ws_options={'sslopt': self.sslopt}
        )
