resource "aws_glue_catalog_database" "databases" {
  for_each = toset(["bronze", "silver", "gold"])

  # Troca qualquer "-" por "_" para o Athena aceitar
  name = replace("climate_platform_${each.key}", "-", "_")
}

resource "aws_glue_crawler" "inmet_crawler" {
  database_name = "climate_platform_bronze" # O nome que corrigimos com underline
  name          = "inmet_bronze_crawler"
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = "s3://climate-platform-bronze-${var.user_name}/bronze/source=inmet/"
  }
}

resource "aws_glue_crawler" "ibge_crawler" {
  database_name = "climate_platform_bronze"
  name          = "ibge_bronze_crawler"
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = "s3://climate-platform-bronze-${var.user_name}/bronze/source=ibge/"
  }
}