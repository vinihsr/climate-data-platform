resource "aws_glue_catalog_database" "bronze_db" {
  name = "climate_platform_bronze"
}

resource "aws_glue_catalog_database" "silver_db" {
  name = "climate_platform_silver"
}