terraform {
  required_version = "~> 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.12"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

locals {
  google_project = "northern-shield-453920-a4"
  google_region  = "us-central1"
  google_zone    = "us-central1-a"
}

provider "google" {
  project = local.google_project
  region  = local.google_region
  zone    = local.google_zone
}

variable "runner_token" {
  type      = string
  sensitive = true
}

# Added available customisation
module "runner-deployment" {
  source = "git::https://gitlab.com/gitlab-org/ci-cd/runner-tools/grit.git//scenarios/google/linux/docker-autoscaler-default"

  google_project = local.google_project
  google_region  = local.google_region
  google_zone    = local.google_zone

  name = "grit-jsfq6xhf"

  gitlab_url = "https://gitlab.com"

  runner_token = var.runner_token

  ephemeral_runner = {
    # disk_type    = "pd-ssd"
    # disk_size    = 50
    machine_type = "n2d-standard-2"
    # source_image = "projects/cos-cloud/global/images/family/cos-stable"
  }
}

output "runner-manager-external-ip" {
  value = module.runner-deployment.runner_manager_external_ip
}