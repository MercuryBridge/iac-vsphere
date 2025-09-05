# Ansible & Terraform for IaC VMware Management

An Infrastructure as Code (IaC) approach defines and provisions infrastructure through code that will be executed automatically, instead of through manual processes. By treating an IT infrastructure as code, organizations can automate management tasks, benefitting from best practices of software development and reducing human error. 

## Table of Contents

<!-- TOC -->
- [Ansible & Terraform for IaC VMware Management](#ansible--terraform-for-iac-vmware-management)
  - [Core Approach](#core-approach)
  - [VM Operations Comparison](#vm-operations-comparison)
    - [VM Operations via GitHub Integration](#vm-operations-via-github-integration)
    - [Infrastructure Drift Management](#infrastructure-drift-management)
  - [Security & State Management](#security--state-management)
  - [Operational Tasks Management](#operational-tasks-management)
  - [Operational Workflow Comparison](#operational-workflow-comparison)
  - [Learning & Maintenance](#learning--maintenance)
  - [Recommendation](#recommendation)
  - [Glossary](#glossary)
<!-- /TOC -->

## Core Approach

Both Ansible and Terraform are IaC tools, though, the programming used by each solution differs.

| Aspect              | Terraform                                   | Ansible                               |
|---------------------|---------------------------------------------|---------------------------------------|
| **Management Model**| Terraform uses an approach called declarative programming, which tries to preserve the configuration of an IT infrastructure by defining a desired state | Ansible uses a procedural (or imperative) programming approach, which tries to preserve the configuration of an IT infrastructure by defining the steps to reach a desired state |
| **Config Format**   | Hashicorp Configuration Language (HCL) | YAML                                  |
| **State Tracking**  | Automatic via tfstate                  | Manual via custom tasks               |

## VM Operations Comparison

### VM Operations via GitHub Integration

| Operation | Terraform | Ansible |
|-----------|-----------|---------|
| **Create VM** | Single `terraform apply` command | Single `ansible-playbook` execution |
| **Delete VM** | Single `terraform destroy` command | Separate cleanup playbook required |
| **Modify VM Resources** | Edit config + apply (Hot Plug: CPU/RAM/Disk up while running, CPU/RAM down requires power off, Disk cannot be reduced due to VMware limitations) | Separate playbook for each modification type + state checking tasks  |
| **Rename VM** | ⚠️  [^1] Destroy + recreate with new name. |  [^2] Configuration mutability - Custom playbook with UUID checking (otherwise creates new VM instead of renaming).|

### Infrastructure Drift Management 

Configuration drift occurs when infra changes due to manual/unapproved/unmonitored actions [^3].

| Scenario | Terraform | Ansible |
|----------|-----------|---------|
| **VM Name Conflict** | Error - cannot create if name exists | Handles gracefully with proper playbook logic |
| **VM Deletion** | Detects drift, can re-create on next apply | Requires playbook for verification and can re-create on next apply |
| **VM Resource Drift** | Detects drift & reconfigures automatically on next apply | Needs custom task to check + reapply configuration |
| **Partial Infrastructure** | Only touches resources in state file | Only touches resources in playbook scope |
| **State Corruption** | State file backup/recovery mechanisms | No state to corrupt, but no change tracking |
| **Cross-Environment Sync** | Workspace isolation with separate state files | Separate inventory files per environment |
| **Rollback Requirements** | State history + version control for rollbacks | Manual playbook versioning + VMware snaphot for rollbacks |

## Security & State Management
[⬆ Back to Table of Contents](#table-of-contents)

| Factor | Terraform | Ansible |
|--------|-----------|---------|
| **Password Management** | Plain text in tfstate files, requires HashiCorp Vault integration with additional security measures | Uses HV plugin lookup, no password leakage in execution |
| **State Complexity** | Requires backend management, state locking, plan/apply workflow | No persistent state to manage |
| **GitHub Actions Integration** | State file security concerns, backend configuration needed | Cleaner integration, no sensitive data persistence |

## Operational Tasks Management
[⬆ Back to Table of Contents](#table-of-contents)

| Task Type         | Terraform                                   | Ansible                                                    |
|-------------------|---------------------------------------------|------------------------------------------------------------|
| VM Provisioning   | ✅ Native support (infrastructure-focused)   | ✅ Native support (can also provision via cloud modules) |
| Daily Operations  | ❌ Not designed for runtime tasks            | ✅ Native support (cron, commands, script execution)     |
| Log Management    | ❌ Needs external tools                      | ✅ Built-in modules for file, shell, cron handling       |
| Disk Operations   | ❌ Only VM-level disk provisioning           | ✅ OS-level disk cleanup, monitoring, management         |
| Service Management| ❌ No service control                        | ✅ systemd, service modules for start/stop/restart       |
| Script Execution  | ❌ Possible via provisioners, not native     | ✅ Native script/shell module support                    |
| Scheduled Tasks   | ❌ Requires external schedulers              | ✅ cron module, ansible-cron                             |
| Log Collection    | ❌ No direct retrieval                       | ✅ fetch, slurp modules for log collection               |
| Health Checks     | ❌ No runtime monitoring capability          | ✅ Playbooks for monitoring, alerting, self-healing      |

## Operational Workflow Comparison
[⬆ Back to Table of Contents](#table-of-contents)

| Workflow | Terraform Approach | Ansible Approach |
|----------|-------------------|------------------|
| **VM + OS Setup** | Terraform (VM) + Separate tool (OS tasks) | Single playbook for end-to-end |
| **Daily Maintenance** | External cron + scripts | Ansible playbooks with cron module |
| **Log Rotation** | Manual scripts on VM | Centralized playbook execution |
| **Disk Cleanup** | SSH + manual scripts | Automated playbook with file module |
| **Service Monitoring** | External monitoring tools | Built-in service status checking |

## Learning & Maintenance
[⬆ Back to Table of Contents](#table-of-contents)

| Consideration | Terraform | Ansible |
|---------------|-----------|---------|
| **Learning Curve** | HCL syntax + Terraform concepts (state, plan, apply, destroy) | YAML + task-based thinking |
| **VMware-Only Environment** | Overkill for single provider | More appropriate scope |
| **Maintenance Overhead** | State management, backend configuration, security hardening | More playbook creation but simpler overall architecture |
| **Operational Complexity** | Plan → Apply → State management cycle | Task execution with manual state verification |

## Recommendation
[⬆ Back to Table of Contents](#table-of-contents)

### For this project, **Ansible** is the recommended solution:

- Supports both **declarative** and **procedural** styles, depending on module behavior
- Best for **VMware or traditional on-premise environments**
- Purpose-built for **configuration management** and **operations**
- Easier adoption for teams managing **VM lifecycle + day-to-day tasks** 
- Ideal for **task-based automation** (configuration, services, daily VM operations)
- Native support for **scripts, services, scheduling, and monitoring**
- Simpler **security and authentication** models
- Smooth integration with **CI/CD pipelines (e.g., GitHub Actions)** without worrying about state files

### Avoid **Terraform** for the following scenarios:

- Primarily focused on public cloud infrastructure provisioning
- Teams not fully aligned with **infrastructure-as-code practices**
- Scenarios where **state management adds unnecessary complexity**
- **Inside-VM operations** (scripts, services, log handling)
- Use cases requiring **runtime monitoring or log collection**
- [Interacting with Vault from Terraform causes any secrets that you read and write to be persisted in both Terraform's state file and in any generated plan files. For any Terraform module that reads or writes Vault secrets, these files should be treated as sensitive and protected accordingly.](https://registry.terraform.io/providers/hashicorp/vault/latest/docs)

## Glossary

[^1]: Configuration immutability means that the configuration (of an infrastructure or an application) can’t be changed. For example, provisioning the newer version of an app requires the previous version to be eliminated and replaced—rather than modified and updated. Resources are destroyed and recreated automatically.
  Terraform uses an immutable infrastructure approach, which can help users get started quickly as they can easily spin up resources, test something, then tear it down. However, depending on the size of the infrastructure, it can become complex and hard to manage. Although Ansible is designed assuming configuration mutability, some automation workflows can be designed to embrace the immutability approach.

[^2]: Configuration mutability means that the configuration (of an infrastructure or an application) can be changed. For example, newer versions of applications can be provisioned by updating or modifying the existing resource instead of eliminating or replacing it.
  Ansible is designed assuming configuration mutability. The advantage of this approach is that the automation workflows are simple to understand and easy to troubleshoot. However, in certain scenarios, it can be challenging to deprovision resources without knowing the correct order of operations.

[^3]: Configuration drift occurs when an infrastructure changes due to manual, unapproved, or unmonitored changes over time—and those changes are not recorded or tracked systematically. Often, these changes are due to emergencies or excessive complexity, factors that can discourage employees from following the established process. As a result, configuration drift is frequent in large organizations.
