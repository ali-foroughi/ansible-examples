import json
import sys
import csv
import shutil
import subprocess
import os
from ruamel.yaml import YAML
from jinja2 import Template


templates_dir = 'templates'
modules = ["mme", "hss", "freediameter", "tls"]

# Get the CSV file name from the command-line argument
csv_file = sys.argv[1]
csv_file_lower = csv_file

# Convert the CSV file to lowercase and save it to /tmp

#csv_file_lower = os.path.join('/tmp', csv_file)
#with open(csv_file, 'r') as file:
#    with open(csv_file_lower, 'w') as output_file:
#        for line in file:
#            output_file.write(line.lower())


def input_output_dir (module_name):
    if module_name in modules:
        output_dir = "output_files/"+ module_name
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir
    else:
        raise ValueError("Invalid module specified: " + module_name)


def mme_generate():
    output_directory = input_output_dir("mme") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV fil
            MME_NAME,CODE,S1AP,S11,S10,HSS_NAME,HSS_IP = row
            
            with open("templates/mme.json") as json_template:
                json_data = json.load(json_template)

            json_data['logger']['file']=  '/root/zcore/install/var/log/open5gs/'+ MME_NAME + '.log'
            json_data['mme']['s1ap'][0]['addr'] =  S1AP
            json_data['mme']['gtpc'][0]['addr'] =  S11
            print (S11)
            json_data['mme']['s10'][0]['addr'] = S10
            json_data['mme']['gummei']['mme_code'] = CODE

            yaml_file = os.path.join(output_directory, MME_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)


def hss_generate():
    output_directory = input_output_dir("hss")

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            MME_NAME,CODE,S1AP,S11,S10,HSS_NAME,HSS_IP = row
            with open("templates/hss.json") as json_template:
                json_data = json.load(json_template)

            json_data['logger']['file']=  '/root/zcore/install/var/log/open5gs/'+ HSS_NAME + '.log'

            yaml_file = os.path.join(output_directory, HSS_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)




def generate_freediameter_files(mme_csv_file, hss_csv_file, mme_template_path, hss_template_path):
    output_directory = input_output_dir("freediameter") 
    # Read the mme.csv file
    mme_entries = []
    
    with open(mme_csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            mme_entries.append(row)
    
    # Read the hss.csv file
    hss_entries = []
    
    with open(hss_csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            hss_entries.append(row)
    
    # Read the mme.conf template and generate configuration files
    with open(mme_template_path, 'r') as template_file:
        mme_template = Template(template_file.read())

    # Generate mme.conf files
    for mme_entry in mme_entries:
        mme_name = mme_entry['MME_NAME']
        mme_ip = mme_entry['S1AP']
        connect_peer_lines = '\n'.join([
            f'ConnectPeer = "{hss_entry["HSS_NAME"]}.localdomain" {{ ConnectTo = "{hss_entry["HSS_IP"]}"; No_TLS; }};'
            for hss_entry in hss_entries
        ])
        mme_config = mme_template.render(MME_NAME=mme_name, MME_IP=mme_ip, CONNECT_PEER_LINES=connect_peer_lines)
        with open(f'{output_directory}/{mme_name}.conf', 'w') as file:
            file.write(mme_config)
            print(f'Generated {output_directory}/{mme_name}.conf')

    # Read the hss.conf template and generate configuration files
    with open(hss_template_path, 'r') as template_file:
        hss_template = Template(template_file.read())

    # Generate hss.conf files
    for hss_entry in hss_entries:
        hss_name = hss_entry['HSS_NAME']
        hss_ip = hss_entry['HSS_IP']
        connect_peer_lines = '\n'.join([
            f'ConnectPeer = "{mme_entry["MME_NAME"]}.localdomain" {{ ConnectTo = "{mme_entry["S1AP"]}"; No_TLS; }};'
            for mme_entry in mme_entries
        ])
        hss_config = hss_template.render(HSS_NAME=hss_name, HSS_IP=hss_ip, CONNECT_PEER_LINES=connect_peer_lines)
        with open(f'{output_directory}/{hss_name}.conf', 'w') as file:
            file.write(hss_config)
            print(f'Generated {output_directory}/{hss_name}.conf')


def generate_tls_certs(mme_csv_file, hss_csv_file):
    output_directory = input_output_dir("tls") 
    with open(mme_csv_file, 'r') as mme_file, open(hss_csv_file, 'r') as hss_file:
        mme_csv_reader = csv.DictReader(mme_file)
        hss_csv_reader = csv.DictReader(hss_file)
        
        mme_entries = list(mme_csv_reader)
        hss_entries = list(hss_csv_reader)
        
        for entry in mme_entries + hss_entries:
            instance_name = entry['MME_NAME'] if 'MME_NAME' in entry else entry['HSS_NAME']
            instance_name = instance_name + '.localdomain'
            print (instance_name)
            cert_output_dir = os.path.join(output_directory, instance_name)
            os.makedirs(cert_output_dir, exist_ok=True)
            cert_script_path = os.path.join(os.path.dirname(__file__), 'certMaker.sh')
            subprocess.run([cert_script_path, instance_name], cwd=cert_output_dir)


mme_generate()
hss_generate()
generate_freediameter_files('mme.csv', 'hss.csv', 'templates/mme.conf.j2', 'templates/hss.conf.j2')
generate_tls_certs('mme.csv', 'hss.csv')
