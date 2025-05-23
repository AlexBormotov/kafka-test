#!/bin/bash

set -eu
set -o pipefail

if [[ "${1:-}" == "--debug" ]]; then
  set -x
  shift
fi

GOOGLE_PROJECT_ID="northern-shield-453920-a4"
GRIT_PROVISIONER_SERVICE_ACCOUNT_NAME="grit-provisioner-auto"
GRIT_PROVISIONER_ROLE_ID="GRITProvisioner"

echo '> Setting up services required for runner provisioning'
gcloud services enable cloudkms.googleapis.com compute.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com --project=$GOOGLE_PROJECT_ID

echo '> Setting up services required for runner execution'
gcloud services enable iamcredentials.googleapis.com oslogin.googleapis.com --project=$GOOGLE_PROJECT_ID

echo '> Preparing role definition file'
temp_dir="$(mktemp --directory)"
provisioner_role_json_path="$(mktemp $temp_dir/grit-provisioner-role.XXXX.json)"
cat <<EOF > $provisioner_role_json_path
{
  "title": "$GRIT_PROVISIONER_ROLE_ID",
  "description": "A role with minimum list of permissions required for GRIT provisioning",
  "includedPermissions": [
    "cloudkms.cryptoKeyVersions.destroy",
    "cloudkms.cryptoKeyVersions.list",
    "cloudkms.cryptoKeyVersions.useToEncrypt",
    "cloudkms.cryptoKeys.create",
    "cloudkms.cryptoKeys.get",
    "cloudkms.cryptoKeys.update",
    "cloudkms.keyRings.create",
    "cloudkms.keyRings.get",
    "compute.disks.create",
    "compute.firewalls.create",
    "compute.firewalls.delete",
    "compute.firewalls.get",
    "compute.instanceGroupManagers.create",
    "compute.instanceGroupManagers.delete",
    "compute.instanceGroupManagers.get",
    "compute.instanceGroups.create",
    "compute.instanceGroups.delete",
    "compute.instanceTemplates.create",
    "compute.instanceTemplates.delete",
    "compute.instanceTemplates.get",
    "compute.instanceTemplates.useReadOnly",
    "compute.instances.create",
    "compute.instances.delete",
    "compute.instances.get",
    "compute.instances.setLabels",
    "compute.instances.setMetadata",
    "compute.instances.setServiceAccount",
    "compute.instances.setTags",
    "compute.networks.create",
    "compute.networks.delete",
    "compute.networks.get",
    "compute.networks.updatePolicy",
    "compute.subnetworks.create",
    "compute.subnetworks.delete",
    "compute.subnetworks.get",
    "compute.subnetworks.use",
    "compute.subnetworks.useExternalIp",
    "compute.zones.get",
    "iam.roles.create",
    "iam.roles.delete",
    "iam.roles.get",
    "iam.roles.list",
    "iam.roles.update",
    "iam.serviceAccounts.actAs",
    "iam.serviceAccounts.create",
    "iam.serviceAccounts.delete",
    "iam.serviceAccounts.get",
    "iam.serviceAccounts.list",
    "resourcemanager.projects.get",
    "resourcemanager.projects.getIamPolicy",
    "resourcemanager.projects.setIamPolicy",
    "storage.buckets.create",
    "storage.buckets.delete",
    "storage.buckets.get",
    "storage.buckets.getIamPolicy",
    "storage.buckets.setIamPolicy"
  ],
  "stage": "BETA"
}
EOF

echo "> Creating $GRIT_PROVISIONER_ROLE_ID role"
gcloud iam roles create $GRIT_PROVISIONER_ROLE_ID --project=$GOOGLE_PROJECT_ID --file="$provisioner_role_json_path" || \
  echo "! $GRIT_PROVISIONER_ROLE_ID role already created"
rm -rf "$temp_dir"

echo "> Creating $GRIT_PROVISIONER_SERVICE_ACCOUNT_NAME service account"
gcloud iam service-accounts create $GRIT_PROVISIONER_SERVICE_ACCOUNT_NAME --project=$GOOGLE_PROJECT_ID \
    --display-name='GRIT provisioner' --description='Service account for GRIT provisioning' || \
  echo "Service account $GRIT_PROVISIONER_SERVICE_ACCOUNT_NAME already created"

echo '> Adding IAM policy binding'
gcloud projects add-iam-policy-binding \
  $GOOGLE_PROJECT_ID \
  --member="serviceAccount:${GRIT_PROVISIONER_SERVICE_ACCOUNT_NAME}@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="projects/${GOOGLE_PROJECT_ID}/roles/${GRIT_PROVISIONER_ROLE_ID}"

echo '> Done'
