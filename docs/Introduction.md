# Introduction

This repository provides infrastructure-as-code to automate the creation of template systems (Ubuntu and Oracle Linux in multiple versions) on VMware vSphere using **HashiCorp Packer**, **Ansible**, and **Serverspec**. By default, VM image artifacts are created from DVD ISO files.

The build process is automated using GitHub Actions and can be triggered manually. You can modify the Packer template to customize the configuration of the virtual machine image.

To use these GitHub Actions workflows, you must provide the following input:

- `Site`: Environment information for the executed site (see `build-env/`)

The provided `Site` value is used by Packer to configure the network settings of the VM template during the build process. These settings are important because they allow the guest operating system to communicate with the outside world and other machines on the network.

It is important to enter the correct `Site` value because the tasks execute commands based on these input values, the directory structure, and file names.  
If an incorrect value is entered, the workflow may not be able to locate the correct directory, leading to errors such as **`No such file or directory`**, and the specified tests will not run.

Therefore, always ensure the correct values are entered to allow the workflow to run successfully and execute the correct tests for the specified environment (e.g., `sat-sg1n`, `prd-sg1n`, etc.).

---

### GitHub Action – Building a Container to Integrate Packer, Ansible, and Serverspec

The `Building a container to integrate Packer - Ansible - Serverspec` workflow automates the process of building a container image with all required tools. This workflow can be triggered manually or via a workflow dispatch event and performs the following steps:

1. **Checks out the source code** from the repository.
2. **Logs into** the GitHub Packages / Docker Hub / Harbor private container registry using credentials (optional).
3. **Sets up Docker Buildx** for multi-platform builds.
4. **Extracts Docker metadata** for tagging and labeling.
5. **Builds the Docker image** and keeps it locally on the GitHub runner.
6. **Pushes the Docker image** to the target container registry (optional).

> **Note:** You can optionally build the container image and keep it locally on the GitHub runner to reuse it in subsequent workflows by referencing its Docker image name.

---

### GitHub Action – Packer Pipeline for Building Golden Image

The `Packer Pipeline for Building Golden Image` workflow automates the process of building a Golden Image using Packer and Ansible.

1. **check-syntax-yml (Check YAML files)**  
   Ensures the quality and consistency of YAML files using the `yamllint` tool.

2. **pre (before_script)**  
   Runs on a self-hosted runner, loads environment variables from the specified environment file (`build-env/`), and prepares variables required for subsequent jobs.

3. **packer-create (Build Packer Template)**  
   Runs on a self-hosted runner, checks out the source code, loads environment variables, initializes Packer, and builds the VM template. After building, Ansible is used to configure the template for the Golden Image.

4. **ansible-config (Run Ansible config template)**  
   Runs Ansible to configure the VM template for Golden Image deployment using inventory files under `ansible/build_site/.../...` and the `template-configuration.yml` playbook.

5. **serverspec-verify (Post-build validation)**  
   Runs Serverspec tests against the built Golden Image to verify OS baseline, services, packages, and security configurations. Uses predefined spec files for each supported OS to perform automated verification before release.
