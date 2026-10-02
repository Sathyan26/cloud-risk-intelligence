resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-data-${data.aws_caller_identity.current.account_id}"
}

# Objects land under raw/ and rejected/ prefixes. Auto-expiring them keeps
# storage cost bounded for a project that's mostly idle between demos.
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "expire-after-retention-window"
    status = "Enabled"

    filter {}

    expiration {
      days = var.raw_data_retention_days
    }
  }
}

resource "aws_s3_bucket_notification" "trigger_validation" {
  bucket = aws_s3_bucket.data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.validate_ingest.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
