locals {
  tags = merge(var.tags, {
    Name = var.domain_name
  })
}

resource "aws_acm_certificate" "cert" {
  domain_name               = var.domain_name
  subject_alternative_names  = ["*.${var.domain_name}"]
  validation_method         = "DNS"
  tags                      = local.tags
}


data "aws_route53_zone" "example" {
  provider     = aws.dnszone
  name         = var.route53_zone_name
  private_zone = var.route53_private_zone
}

resource "aws_route53_record" "example" {
  provider = aws.dnszone

  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.example.zone_id
}
