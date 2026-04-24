resource "aws_glue_catalog_database" "bronze_db" {
  name        = "climate_platform_bronze"
  description = "Dados brutos particionados por dia vindos de INMET, ANA e IBGE."
}

resource "aws_glue_catalog_database" "silver_db" {
  name        = "climate_platform_silver"
  description = "Dados limpos e transformados via Athena (Fact and Dimension tables)."
}

resource "aws_glue_catalog_database" "gold_db" {
  name        = "climate_platform_gold"
  description = "Dados agregados prontos para consumo de business e Dashboards."
}