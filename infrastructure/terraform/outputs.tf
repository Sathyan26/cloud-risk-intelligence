output "s3_bucket_name" {
  value = aws_s3_bucket.data_lake.bucket
}

output "rds_endpoint" {
  value     = aws_db_instance.postgres.address
  sensitive = true
}

output "lambda_function_name" {
  value = aws_lambda_function.validate_ingest.function_name
}
