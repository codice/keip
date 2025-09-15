set -eux

WEBAPP_DIR=operator/webapp

verify_version_bump() {
  potential_tag=$(make --no-print-directory -C $WEBAPP_DIR get-tag)

  # Changes to the Makefile are excluded since they will not change the webhook image
  sh .github/workflows/scripts/shared/verify_changes_update_version.sh $potential_tag $WEBAPP_DIR '-e Makefile$'
}

sh .github/workflows/scripts/shared/verify_current_webapp_img.sh
verify_version_bump
