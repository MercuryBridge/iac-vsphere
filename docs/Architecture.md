# Topology

![Topology](picture/diagram.svg)

# Requirements

**Platform**:

- VMware vSphere 7.0 Update 3D or higher.
- Ansible-Core 2.13 or higher.
- HashiCorp Packer 1.10.0 or higher.
- Serverspec 2.43.0 or higher.

```note
Note: This Github Actions workflow is currently dependent on the SAT Environment
```
# Configuration

<details>
   <summary><i><b>The directory structure of the repository.</b></i></summary> 

   ```console
    ├── ansible
    │   ├── ansible.cfg
    │   ├── clear-template.yml
    │   ├── inventories
    │   │   ├── prd-sg1
    │   │   │   ├── group_vars
    │   │   │   │   └── all.yml
    │   │   │   └── hosts
    │   │   └── sat-sg1
    │   │       ├── group_vars
    │   │       │   └── all.yml
    │   │       └── hosts
   ```
</details>
