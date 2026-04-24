output "pipeline_access_key" {
  value = aws_iam_access_key.pipeline_key.id
}

output "pipeline_secret_key" {
  value     = aws_iam_access_key.pipeline_key.secret
  sensitive = true
}

output "glue_role_arn" {
  value = aws_iam_role.glue_role.arn
}

output "bronze_bucket_name" {
  value = aws_s3_bucket.buckets["bronze"].id
}

output "silver_bucket_name" {
  value = aws_s3_bucket.buckets["silver"].id
}

output "gold_bucket_name" {
  value = aws_s3_bucket.buckets["gold"].id
}

output "athena_results_bucket" {
  value = aws_s3_bucket.buckets["athena-results"].id
}

output "athena_workgroup_name" {
  value = aws_athena_workgroup.main.name
}