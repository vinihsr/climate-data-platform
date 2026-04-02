output "pipeline_access_key" {
  value = aws_iam_access_key.pipeline_key.id
}

output "pipeline_secret_key" {
  value     = aws_iam_access_key.pipeline_key.secret
  sensitive = true
}

output "bronze_bucket" {
  value = aws_s3_bucket.buckets["bronze"].id
}