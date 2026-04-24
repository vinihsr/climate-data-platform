resource "aws_iam_user" "pipeline_user" {
  name = "pipeline-user-${var.user_name}" # Added suffix for uniqueness
}

resource "aws_iam_access_key" "pipeline_key" {
  user = aws_iam_user.pipeline_user.name
}

# Pipeline User Permissions (Kept Admin for your ease, but added suffix)
resource "aws_iam_user_policy_attachment" "pipeline_admin" {
  user       = aws_iam_user.pipeline_user.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}   

# Glue Role Definition
resource "aws_iam_role" "glue_role" {
  name = "GlueServiceRoleClimate-${var.user_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })
}

# Attach Standard Glue Policy
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_athena_access" {
  name = "GlueS3AndAthenaAccess"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::climate-platform-*-${var.user_name}",
          "arn:aws:s3:::climate-platform-*-${var.user_name}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution"
        ]
        Resource = ["*"]
      }
    ]
  })
}