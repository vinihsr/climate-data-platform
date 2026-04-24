locals {
  layers = ["bronze", "silver", "gold", "athena-results"]
}

resource "aws_s3_bucket" "buckets" {
  for_each = toset(local.layers)
  
  bucket = "climate-platform-${each.key}-${var.user_name}"
  
  force_destroy = true 
}

resource "aws_s3_bucket_versioning" "bronze_versioning" {
  bucket = aws_s3_bucket.buckets["bronze"].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_expiry" {
  bucket = aws_s3_bucket.buckets["athena-results"].id
  rule {
    id     = "expire_results"
    status = "Enabled"
    filter {}
    expiration {
      days = 7
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "global_cleanup" {
  for_each = aws_s3_bucket.buckets
  bucket   = each.value.id

  rule {
    id     = "abort_failed_uploads"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}