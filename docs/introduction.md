# Introduction

## Overview

This repository implements enterprise-grade VMware vSphere automation through GitHub Actions with multi-layered security, approval workflows, and comprehensive audit trails.

```mermaid
---
config:
  layout: elk
  look: neo
  theme: neo
---
flowchart LR
 subgraph Github["<br>GitHub"]
        GHA["GitHub Actions"]
        GHS["GitHub Secrets<br>• Vault URL<br>• Vault Token"]
  end
 subgraph On-premises["<br>On-premises (SAT)<br>(Self-Hosted Github Runner)"]
        DC["Docker Container<br>Custom Image"]
        A["Ansible Runner"]
        HV["HashiCorp Vault<br>• SSH Keys<br>• vSphere Creds"]
        VC["VMware vCenter<br>• VM Operations<br>• VM Scan"]
  end
    GHA --> GHS & DC
    DC --> A & HV
    HV --> VC
    GHS --> HV
    A --> VC
```

### Access Control & Security Framework

#### Layer 1: GitHub Repository Access

- Repository collaborator permissions
- Branch protection rules for `main`
- Required PR reviews for `main`

#### Layer 2: Workflow-Level Authorization

Located in `.github/workflows_control/user_access.yml`:

```yaml
---
github_workflows:
  ansible_vsphere_vm_provision:
    main_admin_user:
      - duongvanthanh1992          # Current admin
      - HenryHien                  # ADD: New DevOps engineer

  ansible_vsphere_vm_scan:
    main_admin_user:
      - duongvanthanh1992         # Current admin
      - tieubinh03                # ADD: Security team access

  ansible_vsphere_vm_snapshot:
    main_admin_user:
      - duongvanthanh1992         # Current admin
      - minh.database.admin       # ADD: DB admin for snapshot coordination
```

Only listed `main_admin_user`s can trigger/approve restricted actions in the corresponding workflow.

---

#### Layer 3: Branch-Based Restrictions (Policy) & Environment-Based Authorization

- **Main branch**
  - **SAT**: allowed **only** if the actor is in the workflow’s `main_admin_user`.
      ```yaml
      environment: "sat-sg1n"  # Auto-approve
      ```

  - **PRD (`prd-sg1n`)**: Must `be main_admin_user (same as SAT)` and workflow requires **manual approval**. Only users explicitly assigned as approvers can approve and trigger the deployment.
    ```yaml
    environment: "prd-sg1n"  # ⚠️ MANUAL APPROVAL REQUIRED
    ``` 

- **Non-main branches (feature/*, release/*, hotfix/*, etc.)**
  - **PRD**: **always blocked**.
  - **SAT**: allowed.

- **Enforcement intent**
  - Prevent any production change outside `main`.
  - Require named owners per workflow for production actions.
  - Keep SAT accessible to accelerate CI on all branches.

### Layer 4: Security Validation Pipeline && Pre-commit Security Scanning

- Secret Leak Scan (gitleaks):
  - Detects accidental exposure of credentials, keys, or secrets. Runs on commit, PR, manual trigger, and daily schedule.   
  - **GitLeaks Configuration** (`.github/workflows_control/gitleaks.toml`):
    ```yaml
    name: Secret Leak Scan
    on:
      workflow_dispatch:     # Manual trigger
      pull_request:          # PR validation
      push:                  # Commit validation
      schedule:
        - cron: "0 8 * * *"  # Daily at 8 AM UTC

    jobs:
      scan:
        runs-on: [self-hosted]
        container:
          image: ghcr.io/mercurybridge/iac-vsphere
        env:
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
    ```

- YAML Syntax Validation (yamllint):

  - Ensures Ansible YAML files are valid and consistent. Runs automatically on PRs targeting main.
    ```yaml
    name: Ansible YAML Lint
    on:
      pull_request:
        branches: [main]
        paths: ['ansible/**']       # Only scan Ansible files

    jobs:
      yamllint:
        container:
          image: pipelinecomponents/yamllint
        steps:
          - run: yamllint ansible/  # Validate all Ansible YAML
    ```

### Container Build Process

The workflow uses a custom Ubuntu 24.04-based container with pre-installed tools:

**Container Registry**: `ghcr.io/mercurybridge/iac-vsphere`

```dockerfile
FROM ubuntu:24.04
# Core dependencies: Docker, Python3, Ansible-core >= 2.11.0
# VMware tools: pyvmomi >= 7.0, vsphere-automation-sdk
# Security: HashiCorp Vault (hvac), SSH tools
# Automation: yamllint, yq, git, rsync
```

### Key Dependencies

```yaml
# Python VMware Integration
pyvmomi >= 7.0                    # VMware vSphere API
vsphere-automation-sdk-python     # Advanced vSphere operations

# Ansible Collections
community.vmware                 # VMware modules
community.hashi_vault            # Vault integration
ansible.posix                    # SSH/system operations

# Security & Validation
yamllint >= 1.26.1               # YAML syntax validation
hvac >= 0.10.5                   # HashiCorp Vault client
```








