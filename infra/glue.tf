# Configurações dos Crawlers
locals {
  # Standardizing keys to match the 'source=name' pattern
  bronze_crawlers = {
    "inmet" = "bronze/inmet/"
    "ibge"  = "bronze/ibge/"
    "ana"   = "bronze/ana/"
  }

  silver_crawlers = {
    "fact_clima"    = "silver/fact_clima/"
    "dim_estacoes"  = "silver/dim_estacoes/"
    "dim_municipio" = "silver/dim_municipio/"
  }
}

# --- Bronze Crawlers ---
resource "aws_glue_crawler" "bronze_crawlers" {
  for_each = local.bronze_crawlers

  database_name = aws_glue_catalog_database.bronze_db.name
  name          = "${each.key}_bronze_crawler"
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = "s3://climate-platform-bronze-${var.user_name}/${each.key}/"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      # This forces everything under 'source=x/' into one table
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })
}

# --- Silver Crawlers ---
resource "aws_glue_crawler" "silver_crawlers" {
  for_each = local.silver_crawlers

  database_name = aws_glue_catalog_database.silver_db.name
  name          = "${each.key}_silver_crawler"
  role          = aws_iam_role.glue_role.arn

  s3_target {
    path = "s3://climate-platform-silver-${var.user_name}/${each.value}"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }
}