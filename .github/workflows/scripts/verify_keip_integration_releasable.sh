set -eux

KEIP_INTEGRATION_DIR=keip-integration

verify_version_bump() {
  version=$(mvn -f keip-integration/pom.xml help:evaluate -Dexpression=project.version -q -DforceStdout)
  potential_tag="${GIT_TAG_PREFIX}${version}"
  sh .github/workflows/scripts/shared/verify_changes_update_version.sh $potential_tag $KEIP_INTEGRATION_DIR
}

verify_version_bump
