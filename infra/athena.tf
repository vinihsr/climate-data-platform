resource "aws_athena_workgroup" "main" {
    name = "climate_workgroup"
    configuration {
        enforce_workgroup_configuration = true
        result_configuration {
            output_location = "s3://${aws_s3_bucket.buckets["athena-results"].bucket}/"
        }

        ## 1GB limit = (1073741824)
        bytes_scanned_cutoff_per_query = 1073741824
        engine_version {
            selected_engine_version = "AUTO" # Probably v3
        }
    }
}