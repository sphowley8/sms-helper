# ---------------------------------------------------------------------------
# DELETE THIS FILE once the AWS toll-free registration is approved or rejected.
#
# The phone number cannot be released while its registration is under review.
# Once the registration resolves:
#   1. Delete this file
#   2. Run ./teardown.sh (or terraform destroy) to release the number
#
# Phone number: +18336085237
# Registration: registration-2653dd3b6c044d549fbcfb932570cb81
# ---------------------------------------------------------------------------
resource "aws_pinpointsmsvoicev2_phone_number" "toll_free" {
  iso_country_code            = "US"
  message_type                = "TRANSACTIONAL"
  number_capabilities         = ["SMS"]
  number_type                 = "TOLL_FREE"
  deletion_protection_enabled = false

  lifecycle {
    ignore_changes = all
  }
}
