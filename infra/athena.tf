resource "aws_athena_workgroup" "main" {
  name = "climate_workgroup_${var.user_name}" # Suffix for uniqueness

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.buckets["athena-results"].bucket}/results/"
      
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    # 1GB limit is perfect for a controlled pipeline
    bytes_scanned_cutoff_per_query = 1073741824

    engine_version {
      selected_engine_version = "AUTO" 
    }
  }

  force_destroy = true
}