OPERATOR_DIR=operator
OPERATOR_CONTROLLER_YAML=$OPERATOR_DIR/controller/webhook-deployment.yaml

verify_current_webapp_img() {
  set -eu

  current_webapp_img=$(make --no-print-directory -C webapp get-image-name)
  webapp_image_used=$(yq eval '.spec.template.spec.containers[].image' "$OPERATOR_CONTROLLER_YAML")

  test -n "$current_webapp_img"
  test -n "$webapp_image_used"

  if [ "$webapp_image_used" != "$current_webapp_img" ]; then
    echo "Operator is using $webapp_image_used but should be using the most recent $current_webapp_img."
    exit 1
  fi
}

verify_current_webapp_img
