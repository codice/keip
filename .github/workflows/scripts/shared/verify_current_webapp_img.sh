OPERATOR_DIR=operator
OPERATOR_CONTROLLER_YAML=$OPERATOR_DIR/controller/core-controller.yaml

verify_current_webapp_img() {
  current_webapp_img=$(make --no-print-directory -C operator/webapp get-image-name)
  webapp_image_used=$(yq eval '.spec.template.spec.containers[].image' $OPERATOR_CONTROLLER_YAML)

  test -n "$current_webapp_img"
  test -n "$webapp_image_used"

  error_message="Operator is using $webapp_image_used but should be using the most recent $current_webapp_img."
  test "$webapp_image_used" = "$current_webapp_img" || (echo $error_message && exit 1)
}

verify_current_webapp_img
