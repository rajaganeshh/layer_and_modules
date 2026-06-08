#data "aws_secretsmanager_secret_version" "secret-version" {
#  depends_on = [aws_secretsmanager_secret.secret, aws_secretsmanager_secret_version.secret_version]
#  secret_id  = aws_secretsmanager_secret.secret.id
#}
