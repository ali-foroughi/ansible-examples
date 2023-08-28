# 4G/5G Core configuration

## About

This project is an Ansible playbook for automatically configuring a 4G/5G control plane and data plane based on "zcore".


## Requirements

- Ansible should be installed

```
apt install ansible libguestfs-tools python3-libvirt
```

- If required, install `ansible.community.general` as well. This is needed on the older versions of Ansible.

```
ansible-galaxy collection install community.general
```

- You should have SSH access to the target servers using public key. i,e `ssh-copy-id root@TARGET-IP`


## Usage

- Make sure the correct IP addresses are listed on the `hosts` file.

### For configuring control plane:

- Open `controlPlane.yaml` and make the changes to the `vars` values based on need.

- Run the playbook using this command:
```
ansible-playbook -u root -i hosts controlPlane.yaml
```

### For configuring data plane:

- Open `dataPlane.yaml` and make the changes to the `vars` values based on need.
- Run the playbook using this command:
```
ansible-playbook -u root -i hosts dataPlane.yaml
```
