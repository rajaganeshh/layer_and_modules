# Create Secret
resource "aws_secretsmanager_secret" "secret" {
  name                    = lookup(var.secret, "name", null) != null && lookup(var.secret, "name_prefix", null) == null ? var.secret["name"] : null
  name_prefix             = lookup(var.secret, "name_prefix", null) != null && lookup(var.secret, "name", null) == null ? var.secret["name_prefix"] : null
  description             = lookup(var.secret, "description", null)
  kms_key_id              = lookup(var.secret, "kms_key_id", null)
  policy                  = lookup(var.secret, "policy", null)
  recovery_window_in_days = lookup(var.secret, "recovery_window_in_days", 0)
#  tags                    = lookup(var.secret, "tags", null)
  dynamic "replica" {
    for_each = lookup(var.secret, "replica", null) != null ? var.secret["replica"] : []
    content {
      region     = replica.value.region
      kms_key_id = lookup(replica.value, "kms_key_id", null)
    }
  }
  tags = var.common_tags
}

# Create Secret Version
resource "aws_secretsmanager_secret_version" "secret_version" {
  secret_id     = aws_secretsmanager_secret.secret.id
  secret_string = lookup(var.secret, "secret_string", null) != null && lookup(var.secret, "secret_binary", null) == null ? lookup(var.secret, "secret_string", null) : (lookup(var.secret, "secret_key_value", null) != null ? jsonencode(lookup(var.secret, "secret_key_value", {})) : null)
  secret_binary = lookup(var.secret, "secret_binary", null) != null && lookup(var.secret, "secret_string", null) == null ? base64encode(lookup(var.secret, "secret_binary")) : null
  depends_on    = [aws_secretsmanager_secret.secret]
}