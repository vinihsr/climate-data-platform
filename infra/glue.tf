resource "aws_glue_catalog_database" "databases" {
  for_each = toset(["bronze", "silver", "gold"])

  # Troca qualquer "-" por "_" para o Athena aceitar
  name = replace("climate_platform_${each.key}", "-", "_")
}