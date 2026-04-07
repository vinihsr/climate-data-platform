locals {
    layers = ["bronze", "silver", "gold", "athena-results"]
}

resource "aws_s3_bucket" "buckets" {
  for_each = toset(["bronze", "silver", "gold", "athena-results"])
  
  bucket = replace("climate-platform-${each.key}-${var.user_name}", "_", "-")
  
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
        id = "expire_results"
        status = "Enabled"
        filter {}
        expiration {
            days = 7
        }
    }
}