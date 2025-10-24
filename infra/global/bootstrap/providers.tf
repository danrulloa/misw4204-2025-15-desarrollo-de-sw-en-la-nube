# providers.tf
terraform {
  required_version = ">= 1.6.0"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
  backend "s3" {}
}
provider "aws" { region = var.region }

resource "aws_s3_bucket" "tf_state" { bucket = var.tf_state_bucket }
resource "aws_dynamodb_table" "tf_lock" {
  name         = var.tf_lock_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute { name = "LockID" type = "S" }
}

resource "aws_iam_openid_connect_provider" "gh" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "gh_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals { type = "Federated" identifiers = [aws_iam_openid_connect_provider.gh.arn] }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:ORG/REPO:*"]   # TODO: cambia ORG/REPO
    }
  }
}
resource "aws_iam_role" "ci_role" {
  name               = "anb-ci-role"
  assume_role_policy = data.aws_iam_policy_document.gh_assume.json
}

resource "aws_iam_role_policy_attachment" "ci_admin" {
  role       = aws_iam_role.ci_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

resource "aws_ecr_repository" "api"   { name = "anb-api"   image_tag_mutability = "MUTABLE" }
resource "aws_ecr_repository" "auth"  { name = "anb-auth"  image_tag_mutability = "MUTABLE" }
resource "aws_ecr_repository" "worker"{ name = "anb-worker" image_tag_mutability = "MUTABLE" }
