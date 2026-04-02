# Usuário para o Pipeline (Airflow/dbt)
resource "aws_iam_user" "pipeline_user" {
  name = "pipeline-user"
}

resource "aws_iam_access_key" "pipeline_key" {
  user = aws_iam_user.pipeline_user.name
}

# Role para o Glue assumir
resource "aws_iam_role" "glue_role" {
  name = "GlueServiceRoleClimate"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })
}

# Anexar política de Admin ao usuário do pipeline (Para facilitar o aprendizado inicial)
resource "aws_iam_user_policy_attachment" "pipeline_admin" {
  user       = aws_iam_user.pipeline_user.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}   