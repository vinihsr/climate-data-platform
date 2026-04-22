# Configurações dos Crawlers
locals {
  crawlers = {
    "inmet" = "bronze/source=inmet/"
    "ibge"  = "bronze/source=ibge/"
    "ana"   = "bronze/source=ana/"
  }
}

resource "aws_glue_crawler" "bronze_crawlers" {
  for_each = local.crawlers

  database_name = "climate_platform_bronze"
  name          = "${each.key}_bronze_crawler"
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = "s3://climate-platform-bronze-${var.user_name}/${each.value}"
  }

resource "aws_glue_crawler" "silver_crawler" {
  database_name = aws_glue_catalog_database.silver_db.name
  name          = "silver_data_crawler"
  role          = aws_iam_role.glue_crawler_role.arn # Reuse your existing role

  s3_target {
    path = "s3://${aws_s3_bucket.silver_bucket.id}/silver/dim_estacoes/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      Tables     = { AddOrUpdateBehavior = "MergeNewColumns" } 
    }
  })

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }
}