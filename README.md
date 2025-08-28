# IaC-Driven Automation 

- GitOps-driven VM provisioning and management for vSphere environments via GitHub Actions.

- More details : https://mercurybridge.github.io/iac-vsphere/

## Architecture

```
GitHub Actions → Ansible → HashiCorp Vault → vCenter/vSphere 
```

## Execution Flow

1. **Manual Trigger** → GitHub Actions workflow dispatch
2. **Pre Job** → Load environment variables, set runner
3. **Access Check** → Branch/user authorization validation
4. **Validate Job** → Ansible check mode (`--tags ansible_check`)
   - Vault connectivity
   - vCenter authentication
   - Template existence
   - Infrastructure validation
5. **Apply Job** → Full Ansible execution
   - VM state management
   - Post-deployment validation

## Security

- **Least Privilege**: Role-based workflow access
- **Audit Trail**: Change request tracking
- **Environment Isolation**: Separate configs per environment
- **Secret Zero-Trust**: All credentials via Vault
- **Branch Protection**: Production deployment controls
- **Branch Protection**: Production restricted to `main` branch
- **User Authorization**: Role-based access via `user_access.yml`
- **Environment Gates**: `validation` → `approved` workflow
- **Secret Management**: HashiCorp Vault integration
- **Environments**: `sat-sg1n` (staging), `prd-sg1n` (production)
- **VM Groups**: `vm-db`, `vm-non-db`
- **Inventory**: IP assignments, service owners, states
