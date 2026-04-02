locals {
    layers = ["bronze", "silver", "gold", "athena-results"]
}

resource "aws_s3_bucket" "buckets" {
  for_each = toset(["bronze", "silver", "gold", "athena-results"])
  
  # Troca qualquer "_" por "-" para o S3 não reclamar
  bucket = replace("climate-platform-${each.key}-${var.user_name}", "_", "-")
  
  force_destroy = true 
}

# Enebling versoning on the bronze layer
resource "aws_s3_bucket_versioning" "bronze_versioning" {
    bucket = aws_s3_bucket.buckets["bronze"].id
    versioning_configuration {
        status = "Enabled"
    }
}

# Lifecycle configuration
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