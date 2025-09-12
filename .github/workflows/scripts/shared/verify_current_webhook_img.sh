OPERATOR_DIR=operator
OPERATOR_CONTROLLER_YAML=$OPERATOR_DIR/controller/core-controller.yaml

verify_current_webhook_img() {
  current_keip_img=$(make --no-print-directory -C operator/keip get-image-name)
  keip_image_used=$(yq eval '.spec.template.spec.containers[].image' $OPERATOR_CONTROLLER_YAML)

  test -n "$current_keip_img"
  test -n "$keip_image_used"

  error_message="Operator is using $keip_image_used but should be using the most recent $current_webhook_img."
  test "$keip_image_used" = "$current_keip_img" || (echo $error_message && exit 1)
}

verify_current_keip_img
