terraform {
  # Por enquanto, manteremos o state localmente. 
  # Em projetos avançados, salvaríamos em um S3 remoto.
  backend "local" {
    path = "terraform.tfstate"
  }
}