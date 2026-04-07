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